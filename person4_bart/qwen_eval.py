"""Construct paired Qwen requests, replay exact archive matches, and run local MLX inference."""
from __future__ import annotations

import argparse
import copy
import fcntl
import importlib.metadata
import json
import platform
import time
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

from table3.controlled_baseline.qwen_adapter import flatten_messages, make_qwen_tools, parse_qwen_response

from .core import read_jsonl, sha256, text_hash, unique_index, write_json, write_jsonl
from .generalization import PACKAGE, PROTOCOL, shared_data

HERE = Path(__file__).resolve().parent
BASELINE = HERE.parent / "table3/controlled_baseline/generated/full_factorial_v2"
ARCHIVE = HERE.parent / "qwen-controlled-results.zip"
QWEN_MLX_MODEL = "mlx-community/Qwen2.5-7B-Instruct-4bit"
QWEN_MLX_REVISION = "c26a38f6a37d0a51b4e9a1eb3026530fa35d9fed"


def fetch_qwen_mlx():
    from .model import local_cache

    cache = local_cache()
    from huggingface_hub import snapshot_download

    snapshot = Path(snapshot_download(QWEN_MLX_MODEL, revision=QWEN_MLX_REVISION, token=False,
                    cache_dir=cache / "hub", allow_patterns=["*.safetensors", "*.json", "merges.txt", "README.md"],
                    max_workers=3))
    write_json(HERE / ".cache/qwen-mlx-source.json", {"model_id": QWEN_MLX_MODEL, "revision": QWEN_MLX_REVISION,
               "snapshot_path": str(snapshot), "weight_bytes": sum(p.stat().st_size for p in snapshot.glob("*.safetensors"))})
    print(f"Qwen snapshot ready at {snapshot}")


def json_text(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def request_key(mapping, payload):
    return (mapping["source_case_id"], mapping["order"], mapping["name_mapping"], mapping["seed"], json_text(payload))


def open_archive():
    with zipfile.ZipFile(ARCHIVE) as archive:
        run = "table3/results/qwen-controlled-autodl-full-v1"
        manifest = json.loads(archive.read(f"{run}/run_manifest.json"))
        raw = [json.loads(line) for line in archive.read(f"{run}/raw_responses.jsonl").splitlines()]
    for filename, field in (("controlled_inputs.jsonl", "input_sha256"), ("controlled_mapping.jsonl", "mapping_sha256")):
        if sha256(BASELINE / filename) != manifest[field]:
            raise ValueError(f"Archive hash mismatch: {filename}")
    inputs = unique_index(read_jsonl(BASELINE / "controlled_inputs.jsonl"), "experiment_id")
    maps = unique_index(read_jsonl(BASELINE / "controlled_mapping.jsonl"), "experiment_id")
    outputs = unique_index(raw, "experiment_id")
    if inputs.keys() != maps.keys() or inputs.keys() != outputs.keys():
        raise ValueError("Archive input, map, and raw response IDs must match")
    cache = {request_key(m, inputs[rid]["model_input"]): rid for rid, m in maps.items()}
    if len(cache) != len(inputs):
        raise ValueError("Ambiguous archive payload key")
    return manifest, inputs, maps, outputs, cache


def prepare(run: Path):
    protocol, data = shared_data()
    archive_manifest, baseline_inputs, baseline_maps, archive_raw, cache = open_archive()
    pack = json.loads((PACKAGE / "manifest.json").read_text(encoding="utf-8"))
    if pack["protocol_sha256"] != sha256(PROTOCOL):
        raise ValueError("Evaluation protocol and dataset disagree")
    for filename, expected_hash in pack["files"].items():
        if sha256(PACKAGE / filename) != expected_hash:
            raise ValueError(f"Evaluation dataset hash mismatch: {filename}")
    selected = json.loads((run / "text_evaluation/checkpoint_selection.json").read_text(encoding="utf-8"))
    if selected["protocol_sha256"] != sha256(PROTOCOL) or selected["held_out_package_sha256"] != sha256(PACKAGE / "manifest.json"):
        raise ValueError("Rewrites must use the checkpoint selected for this held-out package")
    test_rewrites = run / "text_evaluation/generalization/rewrites.jsonl"
    rewrites = {"dev": unique_index(read_jsonl(run / "rewrites.jsonl"), "description_id"),
                "test": unique_index(read_jsonl(test_rewrites), "description_id")}
    dev_members = {case: row["source_group_id"] for row in read_jsonl(data / "split_manifest.jsonl")
                   if row["split"] == "dev" for case in row["source_cases"]}
    dev_cases = set(sorted(dev_members, key=text_hash)[:16])
    test_members = unique_index(read_jsonl(PACKAGE / "cases_test.jsonl"), "source_case_id")
    cues = read_jsonl(PACKAGE / "cues.jsonl")
    qwen_inputs, maps, replay, pending, pending_maps, unique_inputs = [], [], [], [], [], []
    local_ids = {}

    for source_id, base in baseline_maps.items():
        if base["description_condition"] != "clean_control":
            continue
        case = base["source_case_id"]
        if case in dev_cases and base["name_mapping"] == "original_suffix1":
            split, group, overlapping, cue_options = "dev", dev_members[case], False, cues[:1]
        elif case in test_members:
            member = test_members[case]
            split, group, overlapping, cue_options = "test", member["source_group_id"], member["query_overlaps_train"], cues
        else:
            continue
        seed_payload = baseline_inputs[source_id]["model_input"]
        for cue in [None, *cue_options]:
            for replace in (False, True):
                condition = ("normalized" if replace else "manipulated") if cue else ("clean_normalized" if replace else "clean_control")
                cue_id = cue["cue_id"] if cue else None
                rid = "::".join(("person4", split, case, condition, cue_id or "clean", base["order"], base["name_mapping"]))
                payload = copy.deepcopy(seed_payload)
                failure_reasons, rewrite_ids = {}, {}
                for tool in payload["function"]:
                    role = base["tool_name_to_role"][tool["name"]]
                    if cue and role == "edited":
                        tool["description"] += " " + cue["text"]
                    if not replace:
                        continue
                    raw_desc = tool["description"]
                    hashed = text_hash(raw_desc)
                    description_id = "desc_" + hashed
                    output = rewrites[split].get(description_id)
                    rewrite_ids[role] = description_id
                    if output is None or output["input_sha256"] != hashed:
                        raise ValueError(f"Missing paired rewrite for {rid}/{role}: {description_id}")
                    if output["status"] != "ok" or output["truncated"] or not output["normalized_description"].strip():
                        failure_reasons[role] = output["error"] or "Invalid rewrite"
                        tool["description"] = ""
                    else:
                        tool["description"] = output["normalized_description"]
                entry = {**base, "experiment_id": rid, "description_condition": condition,
                         "cue_id": cue_id, "cue_text": cue["text"] if cue else None, "split": split,
                         "source_group_id": group, "cue_family": cue["family"] if cue else None,
                         "slice": cue["slice"] if cue else "clean", "query_overlaps_train": overlapping,
                         "rewrite_ids_by_role": rewrite_ids, "normalizer_errors": failure_reasons}
                if payload["question"] != seed_payload["question"] or any(
                    {k: v for k, v in new.items() if k != "description"} != {k: v for k, v in old.items() if k != "description"}
                    for new, old in zip(payload["function"], seed_payload["function"], strict=True)
                ):
                    raise ValueError(f"Non-description field changed: {rid}")
                row = {"experiment_id": rid, "model_input": payload}
                if failure_reasons:
                    entry.update(archive_match_id=None, local_generation_id=None)
                    replay.append({"experiment_id": rid, "status": "error", "error_type": "normalizer_error",
                                   "error": json_text(failure_reasons)})
                else:
                    key = request_key(entry, payload)
                    representative = local_ids.setdefault(key, rid)
                    archived_id = cache.get(key)
                    entry.update(archive_match_id=archived_id, local_generation_id=representative)
                    if representative == rid:
                        unique_inputs.append(row)
                    if archived_id:
                        replay.append({**archive_raw[archived_id], "experiment_id": rid, "archived_experiment_id": archived_id})
                    else:
                        pending.append(row)
                        pending_maps.append(entry)
                qwen_inputs.append(row)
                maps.append(entry)

    unique_index(qwen_inputs, "experiment_id")
    planned = Counter(m["split"] for m in maps)
    expected = {"dev": 16 * 2 * 4, "test": len(test_members) * 4 * (2 + 2 * len(cues))}
    if dict(planned) != expected:
        raise ValueError(f"Expected {expected} requests, built {dict(planned)}")
    destination = run / "qwen"
    destination.mkdir(exist_ok=False)
    # Comparison inputs keep failed cells for scoring. The runner inputs below only include eligible cells.
    for filename, rows in (("comparison_inputs.jsonl", qwen_inputs), ("comparison_mapping.jsonl", maps),
                           ("autodl_replay_raw.jsonl", replay), ("autodl_pending_inputs.jsonl", pending),
                           ("autodl_pending_mapping.jsonl", pending_maps), ("mlx_unique_inputs.jsonl", unique_inputs)):
        if rows:
            write_jsonl(destination / filename, rows)
        else:
            (destination / filename).touch()
    manifest = {"protocol_id": protocol["protocol_id"], "protocol_sha256": sha256(PROTOCOL), "planned": dict(planned),
                "actual_eligible_unique_payloads": len(unique_inputs),
                "normalizer_error_cells": sum(bool(m["normalizer_errors"]) for m in maps),
                "archive_matched": dict(Counter(m["split"] for m in maps if m["archive_match_id"])),
                "archive_pending": dict(Counter(m["split"] for m in pending_maps)),
                "archive_model_revision": archive_manifest["model_revision"], "archive_gpu": archive_manifest["gpu"],
                "archive_expected_chat_template_sha256": archive_manifest["chat_template_sha256"],
                "archive_sha256": sha256(ARCHIVE), "bart_checkpoint_sha256": selected["checkpoint_sha256"],
                "rewrite_sha256": {"dev": sha256(run / "rewrites.jsonl"), "test": sha256(test_rewrites)},
                "files": {p.name: sha256(p) for p in sorted(destination.glob("*.jsonl"))}}
    write_json(destination / "manifest.json", manifest)
    print(json.dumps({k: manifest[k] for k in ("planned", "actual_eligible_unique_payloads", "normalizer_error_cells",
                                               "archive_matched", "archive_pending")}, indent=2))


def heldout_group_scope(maps):
    groups = defaultdict(set)
    for row in maps:
        if row["split"] == "test":
            groups[row["source_group_id"]].add(row["source_case_id"])
    return {group: min(cases, key=text_hash) for group, cases in sorted(groups.items())}


def generate_mlx(root: Path, scope: str):
    import mlx.core as mx
    from mlx_lm import load
    from mlx_lm.generate import BatchGenerator, generation_stream, wired_limit

    plan = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    inputs_path = root / "mlx_unique_inputs.jsonl"
    if plan["files"][inputs_path.name] != sha256(inputs_path):
        raise ValueError("MLX input hash mismatch")
    rows = read_jsonl(inputs_path)
    selected_cases = None
    if scope == "heldout-groups":
        mapping_path = root / "comparison_mapping.jsonl"
        if plan["files"][mapping_path.name] != sha256(mapping_path):
            raise ValueError("MLX comparison mapping hash mismatch")
        maps = read_jsonl(mapping_path)
        selected_cases = heldout_group_scope(maps)
        eligible = {m["local_generation_id"] for m in maps if m["source_case_id"] in selected_cases.values()}
        rows = [r for r in rows if r["experiment_id"] in eligible]
    settings = json.loads((HERE / ".cache/qwen-mlx-source.json").read_text(encoding="utf-8"))
    if (settings["model_id"], settings["revision"]) != (QWEN_MLX_MODEL, QWEN_MLX_REVISION):
        raise ValueError("Local Qwen checkpoint differs from the recorded revision")
    snapshot = Path(settings["snapshot_path"])
    input_size = len(rows)
    cap, concurrent, prefill, checkpoint_size = (512, 16, 8, 24) if selected_cases else (4096, 12, 4, 40)
    destination = root / ("mlx-groups" if selected_cases else "mlx")
    destination.mkdir(exist_ok=True)
    batches = destination / "batches"
    batches.mkdir(exist_ok=True)
    config = {"model_id": settings["model_id"], "revision": settings["revision"], "backend": "MLX Metal",
              "quantization": json.loads((snapshot / "config.json").read_text())["quantization"],
              "mlx": importlib.metadata.version("mlx"), "mlx_lm": importlib.metadata.version("mlx-lm"),
              "transformers": importlib.metadata.version("transformers"), "platform": platform.platform(),
              "input_sha256": plan["files"][inputs_path.name], "max_new_tokens": cap, "decoding": "greedy",
              "completion_batch_size": concurrent, "prefill_batch_size": prefill, "checkpoint_batch_size": checkpoint_size,
              "tokenizer_config_sha256": sha256(snapshot / "tokenizer_config.json"),
              "chat_template_sha256": text_hash(json.loads((snapshot / "tokenizer_config.json").read_text())["chat_template"]),
              "expected_autodl_chat_template_sha256": plan["archive_expected_chat_template_sha256"]}
    if selected_cases:
        config.update(cohort_selection="One held-out case per Person 2 source tool group, minimum SHA-256 of the case ID",
                      scope_reason="Bounded local comparison after timing the first full-scope batch. Selection uses no model outcomes.",
                      selected_cases_by_group=selected_cases)
    if config["chat_template_sha256"] != config["expected_autodl_chat_template_sha256"]:
        raise ValueError("Unexpected Qwen chat template")
    with (destination / ".lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        run_path = destination / "run_manifest.json"
        if run_path.exists() and json.loads(run_path.read_text()) != config:
            raise ValueError("Cannot resume with different MLX settings")
        write_json(run_path, config)
        if not mx.metal.is_available():
            raise RuntimeError("Apple GPU is unavailable to this process")
        mx.set_default_device(mx.gpu)
        start = time.perf_counter()
        model, tokenizer = load(str(snapshot), tokenizer_config={"trust_remote_code": False})
        print(f"Loaded Qwen in {time.perf_counter() - start:.1f}s; {input_size} unique requests", flush=True)
        for offset in range(0, input_size, config["checkpoint_batch_size"]):
            chunk = rows[offset:offset + config["checkpoint_batch_size"]]
            target = batches / f"{offset:06d}.json"
            if target.exists():
                completed = json.loads(target.read_text())
                if [r["experiment_id"] for r in completed["responses"]] != [r["experiment_id"] for r in chunk]:
                    raise ValueError(f"Stored batch IDs differ: {target}")
                continue
            started = time.perf_counter()
            prompts, adapters, hashes = [], [], []
            for row in chunk:
                payload = row["model_input"]
                messages = flatten_messages(payload["question"], row["experiment_id"])
                tools, names = make_qwen_tools(payload["function"])
                prompt = tokenizer.apply_chat_template(messages, tools=tools, tokenize=False, add_generation_prompt=True)
                prompts.append(tokenizer.encode(prompt, add_special_tokens=False))
                hashes.append(text_hash(prompt))
                adapters.append(names)
            generator = BatchGenerator(model, stop_tokens=tokenizer.eos_token_ids,
                                       completion_batch_size=concurrent, prefill_batch_size=prefill)
            uids = generator.insert(prompts, cap)
            tokens = {uid: [] for uid in uids}
            stop_reason = {}
            with wired_limit(model, [generation_stream]):
                while responses := generator.next():
                    for response in responses:
                        tokens[response.uid].append(response.token)
                        if response.finish_reason:
                            stop_reason[response.uid] = response.finish_reason
            if stop_reason.keys() != tokens.keys():
                raise RuntimeError("MLX returned an incomplete generation batch")
            results = []
            for row, uid, prompt_ids, prompt_hash, names in zip(chunk, uids, prompts, hashes, adapters, strict=True):
                raw_text = tokenizer.decode(tokens[uid], skip_special_tokens=False, clean_up_tokenization_spaces=False)
                calls, errors = parse_qwen_response(raw_text, names)
                results.append({"experiment_id": row["experiment_id"], "status": "ok", "finish_reason": stop_reason[uid],
                                "raw_text": raw_text, "parsed_calls": calls, "parse_errors": errors,
                                "prompt_sha256": prompt_hash, "input_tokens": len(prompt_ids), "output_tokens": len(tokens[uid])})
            seconds = round(time.perf_counter() - started, 3)
            tmp = target.with_suffix(".tmp")
            write_json(tmp, {"seconds": seconds, "peak_memory_bytes": mx.get_peak_memory(), "responses": results})
            tmp.replace(target)
            print(f"{offset + len(chunk)}/{input_size} unique requests, latest batch {seconds:.1f}s", flush=True)
        completed = [json.loads(p.read_text()) for p in sorted(batches.glob("*.json"))]
        outputs = [row for batch in completed for row in batch["responses"]]
        if [r["experiment_id"] for r in outputs] != [r["experiment_id"] for r in rows]:
            raise RuntimeError("MLX raw output coverage is incomplete")
        write_jsonl(destination / "raw_unique.jsonl", outputs)
        write_json(destination / "run_status.json", {"requests": len(outputs), "status": "complete",
                   "generation_batch_seconds": sum(b["seconds"] for b in completed),
                   "peak_memory_bytes": max(b["peak_memory_bytes"] for b in completed),
                   "finish_reasons": dict(Counter(row["finish_reason"] for row in outputs)),
                   "parse_errors": sum(bool(row["parse_errors"]) for row in outputs)})


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("command", choices=["prepare", "fetch-mlx-model", "generate-mlx"])
    cli.add_argument("--run", type=Path)
    cli.add_argument("--scope", choices=["all", "heldout-groups"], default="all")
    args = cli.parse_args()
    if args.command == "fetch-mlx-model":
        fetch_qwen_mlx()
    elif args.run is None:
        cli.error("--run is required for prepare and generate-mlx")
    elif args.command == "prepare":
        prepare(args.run.resolve())
    else:
        generate_mlx(args.run.resolve() / "qwen", args.scope)
