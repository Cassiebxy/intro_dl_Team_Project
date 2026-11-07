#!/usr/bin/env python3
"""Resumable one-GPU Qwen inference for controlled_baseline JSONL inputs."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
from qwen_adapter import flatten_messages, make_qwen_tools, parse_qwen_response, read_jsonl, sha256_file

DEFAULT_INPUT = HERE / "generated" / "controlled_inputs.jsonl"
DEFAULT_MAPPING = HERE / "generated" / "controlled_mapping.jsonl"
DEFAULT_OUT = HERE / "results" / "qwen-controlled-factorial-v1"
DEFAULT_MODEL = Path("/scratch/bjfu/mzhao9/Qwen2.5-7B-Instruct")
FULL_REQUESTS = 258 * 7 * 2 * 2


def utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def append_fsync(path: Path, row: dict) -> None:
    data = (json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    try:
        with os.fdopen(fd, "ab", closefd=False) as f:
            f.write(data)
            f.flush()
            os.fsync(fd)
    finally:
        os.close(fd)


def load_checkpoint(path: Path, valid_ids: set[str]) -> dict[str, dict]:
    if not path.exists():
        return {}
    raw = path.read_bytes()
    if raw and not raw.endswith(b"\n"):
        tail = raw.rfind(b"\n")
        raw = raw[:tail + 1] if tail >= 0 else b""
        path.write_bytes(raw)
    result = {}
    for line_no, line in enumerate(raw.decode("utf-8").splitlines(), 1):
        row = json.loads(line)
        rid = row.get("experiment_id")
        if rid not in valid_ids or rid in result:
            raise ValueError(f"Invalid/duplicate checkpoint ID at line {line_no}: {rid}")
        result[rid] = row
    return result


def load_attempt_counts(path: Path, valid_ids: set[str]) -> dict[str, int]:
    counts: dict[str, int] = {}
    if not path.exists():
        return counts
    raw = path.read_bytes()
    if raw and not raw.endswith(b"\n"):
        tail = raw.rfind(b"\n")
        raw = raw[:tail + 1] if tail >= 0 else b""
        path.write_bytes(raw)
    for line_no, line in enumerate(raw.decode("utf-8").splitlines(), 1):
        row = json.loads(line)
        rid = row.get("experiment_id")
        if rid not in valid_ids:
            raise ValueError(f"Unknown ID in attempts log line {line_no}: {rid}")
        if row.get("status") == "started":
            counts[rid] = counts.get(rid, 0) + 1
    return counts


def write_checkpoint(path: Path, rows: dict[str, dict], order: dict[str, int]) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8", newline="\n") as f:
        for rid in sorted(rows, key=order.__getitem__):
            f.write(json.dumps(rows[rid], ensure_ascii=False, separators=(",", ":")) + "\n")
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def validate(input_rows: list[dict], mappings: list[dict]) -> dict[str, dict]:
    input_by_id = {r.get("experiment_id"): r for r in input_rows}
    mapping_by_id = {r.get("experiment_id"): r for r in mappings}
    if len(input_by_id) != len(input_rows) or input_by_id.keys() != mapping_by_id.keys():
        raise ValueError("Input/mapping rows are duplicated or have mismatched IDs")
    for rid, row in input_by_id.items():
        payload, m = row.get("model_input", {}), mapping_by_id[rid]
        if set(row) != {"experiment_id", "model_input"} or set(payload) != {"question", "function"}:
            raise ValueError(f"{rid}: only model_input may be sent to Qwen")
        if len(payload["function"]) != 2 or m["order"] not in {"original_first", "edited_first"}:
            raise ValueError(f"{rid}: invalid tool count/order")
        names = [f["name"] for f in payload["function"]]
        if len(set(names)) != 2 or set(names) != set(m["tool_name_to_role"]):
            raise ValueError(f"{rid}: tool names do not match role mapping")
        if set(m["tool_name_to_role"].values()) != {"original", "edited"}:
            raise ValueError(f"{rid}: incomplete role mapping")
        flatten_messages(payload["question"], rid)
        make_qwen_tools(payload["function"])
        if not isinstance(m.get("expected"), list) or len(m["expected"]) != 2:
            raise ValueError(f"{rid}: missing two role-aligned answer sets")
        if not isinstance(m.get("seed"), int):
            raise ValueError(f"{rid}: missing paired seed")
    return mapping_by_id


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    ap.add_argument("--mapping", type=Path, default=DEFAULT_MAPPING)
    ap.add_argument("--output-dir", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--model-dir", type=Path, default=DEFAULT_MODEL)
    ap.add_argument("--limit", type=int, default=16, help="Default 16-request smoke; full run requires --allow-full-run")
    ap.add_argument("--allow-full-run", action="store_true")
    ap.add_argument("--retry-errors", action="store_true")
    ap.add_argument("--max-new-tokens", type=int, default=4096)
    ap.add_argument("--validate-only", action="store_true")
    args = ap.parse_args()
    if not 1 <= args.limit <= FULL_REQUESTS:
        ap.error(f"--limit must be in 1..{FULL_REQUESTS}")
    if args.limit > 16 and not (args.allow_full_run and args.limit == FULL_REQUESTS):
        ap.error(f"Runs over 16 require --limit {FULL_REQUESTS} --allow-full-run")
    if args.allow_full_run and args.limit != FULL_REQUESTS:
        ap.error("--allow-full-run requires the complete 7,224-request factorial")
    if not 1 <= args.max_new_tokens <= 4096:
        ap.error("--max-new-tokens must be in 1..4096")

    inputs = read_jsonl(args.input)
    maps = read_jsonl(args.mapping)
    mapping_by_id = validate(inputs, maps)
    if args.validate_only:
        print(json.dumps({"validation": "PASS", "requests": len(inputs),
                          "selected_limit": args.limit, "unique_cases": len({m['source_case_id'] for m in maps})}, indent=2))
        return 0
    import fcntl
    if not args.model_dir.is_dir():
        raise FileNotFoundError(args.model_dir)
    for filename in ("config.json", "tokenizer_config.json"):
        if not (args.model_dir / filename).is_file():
            raise FileNotFoundError(args.model_dir / filename)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    lock_fd = os.open(args.output_dir / "run.lock", os.O_CREAT | os.O_WRONLY, 0o600)
    try:
        fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError as exc:
        os.close(lock_fd)
        raise RuntimeError("Another run owns this controlled output directory") from exc
    try:
        results_path = args.output_dir / "raw_responses.jsonl"
        attempts_path = args.output_dir / "attempts.jsonl"
        manifest_path = args.output_dir / "run_manifest.json"
        manifest = {
            "input_sha256": sha256_file(args.input), "mapping_sha256": sha256_file(args.mapping),
            "model_dir": str(args.model_dir.resolve()), "dtype": "bfloat16",
            "seed_implementation": "torch.manual_seed + torch.cuda.manual_seed_all before each request",
            "model_config_sha256": sha256_file(args.model_dir / "config.json"),
            "tokenizer_config_sha256": sha256_file(args.model_dir / "tokenizer_config.json"),
            "decoding": {"do_sample": True, "temperature": 0.01, "top_p": 1.0,
                         "top_k": 0, "repetition_penalty": 1.0,
                         "seed_policy": "same SHA256(case_id)-derived seed across factorial cells"},
            "max_new_tokens": args.max_new_tokens,
        }
        if manifest_path.exists():
            old = json.loads(manifest_path.read_text(encoding="utf-8"))
            if any(old.get(k) != v for k, v in manifest.items()):
                raise ValueError("Resume manifest mismatch; use a new output directory")
        elif results_path.exists() or attempts_path.exists():
            raise ValueError("Found output without manifest; refusing unsafe resume")
        else:
            manifest["created_at_utc"] = utc()
            manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

        previous = load_checkpoint(results_path, set(mapping_by_id))
        selected = inputs[:args.limit]
        todo = [r for r in selected if r["experiment_id"] not in previous or
                (args.retry_errors and previous[r["experiment_id"]].get("status") == "error")]
        if not todo:
            print("All selected requests are checkpointed; no model initialization needed.", flush=True)
            return 0

        import torch
        import transformers
        from transformers import AutoModelForCausalLM, AutoTokenizer
        if not torch.cuda.is_available() or torch.cuda.device_count() != 1:
            raise RuntimeError("Run inside a single-GPU Slurm allocation")
        torch.cuda.set_device(0)
        props = torch.cuda.get_device_properties(0)
        if "A100" not in props.name or props.total_memory < 35 * 1024**3:
            raise RuntimeError(f"Expected one A100 40GB; found {props.name}")
        if not torch.cuda.is_bf16_supported():
            raise RuntimeError("CUDA device does not support BF16")
        print(f"Loading local Qwen from {args.model_dir}", flush=True)
        load_started = time.perf_counter()
        tokenizer = AutoTokenizer.from_pretrained(args.model_dir, local_files_only=True, trust_remote_code=False)
        model = AutoModelForCausalLM.from_pretrained(
            args.model_dir, local_files_only=True, trust_remote_code=False, torch_dtype=torch.bfloat16,
        ).to("cuda:0").eval()
        torch.cuda.synchronize()
        model_load_seconds = time.perf_counter() - load_started
        runtime = {**manifest, "torch": torch.__version__, "transformers": transformers.__version__,
                   "cuda": torch.version.cuda, "gpu": props.name,
                   "model_revision": getattr(model.config, "_commit_hash", None),
                   "chat_template_sha256": hashlib.sha256((tokenizer.chat_template or "").encode()).hexdigest(),
                   "model_load_seconds": model_load_seconds,
                   "model_load_peak_gpu_memory_bytes": torch.cuda.max_memory_allocated(0)}
        manifest_path.write_text(json.dumps(runtime, indent=2) + "\n", encoding="utf-8")
        print(f"model_loaded_seconds={model_load_seconds:.2f} peak_gpu_memory_bytes={torch.cuda.max_memory_allocated(0)}", flush=True)

        attempt_counts = load_attempt_counts(attempts_path, set(mapping_by_id))
        order = {r["experiment_id"]: i for i, r in enumerate(inputs)}
        all_rows = dict(previous)
        for index, row in enumerate(todo, 1):
            rid = row["experiment_id"]
            mapping = mapping_by_id[rid]
            payload = row["model_input"]
            messages = flatten_messages(payload["question"], rid)
            tools, wire_to_canonical = make_qwen_tools(payload["function"])
            start = time.perf_counter()
            attempt_number = attempt_counts.get(rid, 0) + 1
            started = {"experiment_id": rid, "attempt": attempt_number, "status": "started", "started_at_utc": utc()}
            append_fsync(attempts_path, started)
            attempt_counts[rid] = attempt_number
            torch.cuda.reset_peak_memory_stats(0)
            try:
                prompt = tokenizer.apply_chat_template(messages, tools=tools, tokenize=False, add_generation_prompt=True)
                prompt_hash = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
                encoded = tokenizer(prompt, return_tensors="pt", add_special_tokens=False)
                input_tokens = int(encoded["input_ids"].shape[-1])
                encoded = {k: v.to("cuda:0") for k, v in encoded.items()}
                torch.manual_seed(mapping["seed"])
                torch.cuda.manual_seed_all(mapping["seed"])
                with torch.inference_mode():
                    output = model.generate(**encoded, max_new_tokens=args.max_new_tokens,
                        do_sample=True, temperature=0.01, top_p=1.0, top_k=0,
                        repetition_penalty=1.0, use_cache=True,
                        pad_token_id=tokenizer.eos_token_id)
                torch.cuda.synchronize()
                generated = output[0, input_tokens:]
                raw = tokenizer.decode(generated, skip_special_tokens=False, clean_up_tokenization_spaces=False)
                parsed, errors = parse_qwen_response(raw, wire_to_canonical)
                result = {"experiment_id": rid, "attempt": attempt_number, "status": "ok", "raw_text": raw,
                          "parsed_calls": parsed, "parse_errors": errors,
                          "prompt_sha256": prompt_hash, "seed": mapping["seed"], "input_tokens": input_tokens,
                          "output_tokens": int(generated.numel()),
                          "elapsed_seconds": time.perf_counter() - start,
                          "peak_gpu_memory_bytes": torch.cuda.max_memory_allocated(0),
                          "finish_reason": "length" if generated.numel() >= args.max_new_tokens else "stop",
                          "finished_at_utc": utc()}
            except Exception as exc:
                result = {"experiment_id": rid, "attempt": attempt_number, "status": "error", "error_type": type(exc).__name__,
                          "error": str(exc), "elapsed_seconds": time.perf_counter() - start,
                          "finished_at_utc": utc()}
            append_fsync(attempts_path, result)
            all_rows[rid] = result
            write_checkpoint(results_path, all_rows, order)
            print(f"progress={index}/{len(todo)} status={result['status']} id={rid} elapsed={result['elapsed_seconds']:.2f}s", flush=True)
        print(f"checkpointed={len(all_rows)} selected={len(selected)} output={results_path}", flush=True)
        return 0
    finally:
        fcntl.flock(lock_fd, fcntl.LOCK_UN)
        os.close(lock_fd)


if __name__ == "__main__":
    raise SystemExit(main())
