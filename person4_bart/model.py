"""Local checkpoint loading and description-only inference."""
from __future__ import annotations

import gc
import importlib.metadata
import json
import os
import platform
import subprocess
import sys
import time
from pathlib import Path

from . import SCHEMA_VERSION
from .core import text_hash, write_json

HERE = Path(__file__).resolve().parent


def local_cache() -> Path:
    root = HERE / ".cache" / "huggingface"
    os.environ["HF_HOME"] = str(root)
    os.environ["HF_HUB_CACHE"] = str(root / "hub")
    os.environ["HF_HUB_DISABLE_IMPLICIT_TOKEN"] = "1"
    os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
    os.environ["HF_HUB_DISABLE_XET"] = "1"
    os.environ["TOKENIZERS_PARALLELISM"] = "false"
    return root


def fetch_model() -> dict:
    cache = local_cache()
    from huggingface_hub import snapshot_download

    model_id = "facebook/bart-base"
    protocol = json.loads((HERE / "protocols/shared_bfcl_v1.json").read_text(encoding="utf-8"))
    revision = protocol["bart_base_revision"]
    weights = "model.safetensors"
    patterns = [weights, "config.json", "generation_config.json", "merges.txt", "vocab.json",
                "tokenizer.json", "tokenizer_config.json", "special_tokens_map.json", "README.md"]
    snapshot = snapshot_download(model_id, revision=revision, token=False,
                                 cache_dir=cache / "hub", allow_patterns=patterns,
                                 max_workers=2)
    record = {"model_id": model_id, "revision": revision, "snapshot_path": snapshot,
              "weight_file": weights, "downloaded_files": sorted(p.name for p in Path(snapshot).iterdir()),
              "purpose": "Pinned public BART-base initialization"}
    write_json(HERE / "model_source.json", record)
    return record


def model_path(given: str | None) -> Path:
    if given:
        path = Path(given).expanduser().resolve()
    else:
        source = HERE / "model_source.json"
        if not source.exists():
            raise FileNotFoundError("Run `python -m person4_bart fetch-model` first, or provide --model with a local checkpoint")
        path = Path(json.loads(source.read_text())["snapshot_path"])
    if not path.is_dir() or not (path / "config.json").is_file():
        raise FileNotFoundError(f"Local checkpoint not found: {path}")
    return path


def device_for(requested: str = "auto") -> str:
    import torch
    if requested == "auto":
        return "cuda" if torch.cuda.is_available() else ("mps" if torch.backends.mps.is_available() else "cpu")
    if requested == "mps" and not torch.backends.mps.is_available():
        raise RuntimeError("MPS is unavailable in this process. Check environment or macOS process permissions; CPU fallback is not automatic for --device mps.")
    if requested == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA is unavailable")
    return requested


def sync(device: str) -> None:
    import torch
    if device == "mps":
        torch.mps.synchronize()
    elif device == "cuda":
        torch.cuda.synchronize()


def memory(device: str) -> dict:
    import psutil
    import torch
    info = {"process_rss_bytes": psutil.Process().memory_info().rss}
    if device == "mps":
        info.update(mps_allocated_bytes=torch.mps.current_allocated_memory(),
                    mps_driver_allocated_bytes=torch.mps.driver_allocated_memory())
    elif device == "cuda":
        info.update(cuda_allocated_bytes=torch.cuda.memory_allocated(),
                    cuda_peak_allocated_bytes=torch.cuda.max_memory_allocated())
    return info


def environment(check: bool = False) -> dict:
    import psutil
    import torch
    report = {"python": sys.version, "python_executable": sys.executable,
              "platform": platform.platform(), "architecture": platform.machine(),
              "memory_bytes": psutil.virtual_memory().total,
              "mps_built": torch.backends.mps.is_built(), "mps_available": torch.backends.mps.is_available(),
              "cuda_available": torch.cuda.is_available(),
              "mps_cpu_fallback_env": os.environ.get("PYTORCH_ENABLE_MPS_FALLBACK"),
              "packages": {}}
    for name in ("torch", "transformers", "tokenizers", "huggingface-hub", "safetensors", "numpy", "psutil", "matplotlib"):
        try:
            report["packages"][name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            report["packages"][name] = None
    if platform.system() == "Darwin":
        p = subprocess.run(["/usr/sbin/system_profiler", "-json", "SPHardwareDataType"], capture_output=True, text=True, timeout=20)
        if p.returncode == 0:
            row = json.loads(p.stdout)["SPHardwareDataType"][0]
            report["hardware"] = {k: row.get(k) for k in ("machine_name", "chip_type", "physical_memory")}
    if check:
        device = device_for()
        x = torch.tensor([2.0], device=device, requires_grad=True)
        (x * x).sum().backward()
        sync(device)
        report["forward_backward_check"] = {"device": device, "gradient": float(x.grad.detach().cpu()[0]),
                                             "passed": float(x.grad.detach().cpu()[0]) == 4.0}
    return report


def load_model(path: Path, device: str):
    local_cache()
    from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(path, local_files_only=True, use_fast=True)
    tokenizer.padding_side = "right"
    model = AutoModelForSeq2SeqLM.from_pretrained(path, local_files_only=True, attn_implementation="eager").float().to(device)
    # The original checkpoint carries summarization-era beam/no-repeat options.
    # Clear those legacy config values and define description-rewriting decoding.
    for key, value in {"early_stopping": False, "num_beams": 1, "no_repeat_ngram_size": 0,
                       "forced_bos_token_id": None}.items():
        setattr(model.config, key, value)
        setattr(model.generation_config, key, value)
    model.generation_config.forced_bos_token_id = tokenizer.bos_token_id
    model.generation_config.forced_eos_token_id = None
    model.generation_config.do_sample = False
    model.eval()
    return tokenizer, model


def release(device: str) -> None:
    import torch
    gc.collect()
    if device == "mps":
        torch.mps.empty_cache()
    elif device == "cuda":
        torch.cuda.empty_cache()


def generate(model, tokenizer, inputs: list[dict], *, run_id: str, device: str,
             batch_size: int = 2, max_input_tokens: int = 256, max_new_tokens: int = 96,
             prefix: str = "", input_based_limit: bool = False) -> list[dict]:
    """Generate with a fixed or input-derived length limit."""
    import torch
    if batch_size < 1 or max_input_tokens < 2 or max_new_tokens < 1:
        raise ValueError("Invalid generation limits/batch size")
    if max_input_tokens > model.config.max_position_embeddings:
        raise ValueError("max_input_tokens exceeds model context")
    if max_new_tokens + 1 > model.config.max_position_embeddings:
        raise ValueError("max_new_tokens exceeds decoder context")
    results = {}
    pending = []
    for row in inputs:
        if set(row) != {"description_id", "input_description"}:
            raise ValueError("Only description_id/input_description may enter normalizer inference")
        count = len(tokenizer(prefix + row["input_description"], truncation=False)["input_ids"])
        output = {"schema_version": SCHEMA_VERSION, "run_id": run_id, "description_id": row["description_id"],
                  "input_sha256": text_hash(row["input_description"]), "normalized_description": "",
                  "status": "error", "error": None, "input_tokens": count, "output_tokens": 0,
                  "truncated": False, "input_truncated": False, "latency_seconds": None,
                  "max_new_tokens": None}
        results[row["description_id"]] = output
        if count > max_input_tokens:
            output["error"] = f"input_too_long: {count} > {max_input_tokens}; input was not truncated"
        else:
            pending.append(row)
    model.eval()
    with torch.inference_mode():
        for offset in range(0, len(pending), batch_size):
            rows = pending[offset:offset + batch_size]
            start = time.perf_counter()
            cap = max_new_tokens
            if input_based_limit:
                longest = max(results[row["description_id"]]["input_tokens"] for row in rows)
                cap = min(max_new_tokens, max(64, 2 * longest))
            for row in rows:
                results[row["description_id"]]["max_new_tokens"] = cap
            try:
                encoded = tokenizer([prefix + r["input_description"] for r in rows], return_tensors="pt", padding=True, truncation=False).to(device)
                sequences = model.generate(**encoded, do_sample=False, num_beams=1, max_new_tokens=cap,
                                           early_stopping=False, no_repeat_ngram_size=0,
                                           forced_bos_token_id=tokenizer.bos_token_id,
                                           forced_eos_token_id=None, use_cache=True)
                sync(device)
                elapsed = time.perf_counter() - start
                for row, sequence in zip(rows, sequences.detach().cpu().tolist()):
                    new = sequence[1:]  # BART prepends its decoder start token.
                    if tokenizer.eos_token_id in new:
                        new = new[:new.index(tokenizer.eos_token_id) + 1]
                    else:
                        while new and new[-1] == tokenizer.pad_token_id:
                            new.pop()
                    text = tokenizer.decode(new, skip_special_tokens=True, clean_up_tokenization_spaces=False).strip()
                    capped = len(new) >= cap and tokenizer.eos_token_id not in new
                    error = "generation_limit_reached" if capped else ("empty_output" if not text else None)
                    results[row["description_id"]].update(normalized_description=text, status="error" if error else "ok",
                                                          error=error, output_tokens=len(new), truncated=capped,
                                                          latency_seconds=round(elapsed / len(rows), 6))
            except (RuntimeError, ValueError) as exc:
                for row in rows:
                    results[row["description_id"]]["error"] = f"{type(exc).__name__}: {str(exc)[:400]}"
                release(device)
    return [results[r["description_id"]] for r in inputs]
