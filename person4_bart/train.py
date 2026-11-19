"""Full-parameter supervised BART training with auditable local outputs."""
from __future__ import annotations

import json
import math
import random
import time
from pathlib import Path

from .core import audit, inference_rows, load_pairs, save_report, sha256, validate_splits, write_json, write_jsonl
from .model import HERE, device_for, environment, generate, load_model, memory, model_path, release, sync


def plot_history(history, out: Path, shared: bool) -> None:
    import os
    os.environ["MPLCONFIGDIR"] = str(HERE / ".cache" / "matplotlib")
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    epochs = [r["epoch"] for r in history]
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.8))
    axes[0].plot(epochs, [r["train_token_nll"] for r in history], "o-", label="Train")
    axes[0].plot(epochs, [r["dev_token_nll"] for r in history], "o-", label="Seen-format dev" if shared else "Synthetic dev")
    axes[0].set(xlabel="Epoch", ylabel="Token-averaged NLL", title="BART-base training")
    axes[0].legend()
    axes[1].plot(epochs, [100 * r["dev_exact_match_rate"] for r in history], "o-", color="#25634d")
    axes[1].set(xlabel="Epoch", ylabel="Exact match (%)", ylim=(-3, 103),
                title="BFCL development rewrites" if shared else "Synthetic development rewrites")
    for axis in axes:
        axis.set_xticks(epochs)
    for axis in axes:
        axis.grid(alpha=0.2)
    fig.tight_layout()
    fig.savefig(out / "training_curves.png", dpi=160)
    plt.close(fig)


def train(args) -> dict:
    import numpy as np
    import torch
    protocol = None
    if args.protocol:
        protocol = json.loads(args.protocol.read_text(encoding="utf-8"))
        data = HERE.parent / protocol["shared_data"]
        manifest_path = data / "manifest.json"
        if sha256(manifest_path) != protocol["shared_data_manifest_sha256"]:
            raise ValueError("Shared dataset manifest differs from the recorded protocol")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        for split in ("train", "dev"):
            filename = f"pairs_{split}.jsonl"
            path = data / filename
            if sha256(path) != manifest["hashes"][filename]:
                raise ValueError(f"Shared dataset hash mismatch: {filename}")
            setattr(args, split, path)
        for name, value in protocol["training"].items():
            setattr(args, name, value)
        if args.model and model_path(args.model) != model_path(None):
            raise ValueError("The shared protocol starts from the pinned original BART-base snapshot")
        args.model = None
    if min(args.epochs, args.batch_size, args.accumulation_steps, args.patience) < 1:
        raise ValueError("Epochs, batch size, accumulation steps and patience must be positive")
    if args.learning_rate <= 0 or not math.isfinite(args.learning_rate):
        raise ValueError("Invalid learning rate")
    pairs_train = load_pairs(args.train, "train")
    pairs_dev = load_pairs(args.dev, "dev")
    split_info = validate_splits(pairs_train, pairs_dev)
    selection_dev = pairs_dev
    if protocol:
        selection_dev = [row for row in pairs_dev if row.get("variant") != protocol["excluded_selection_variant"]]
        if not selection_dev or len(selection_dev) == len(pairs_dev):
            raise ValueError("Expected seen-wording selection rows and a separate development wording probe")
        split_info["checkpoint_selection_dev_examples"] = len(selection_dev)
    device = device_for(args.device)
    source = model_path(args.model)
    if protocol and source.name != protocol["bart_base_revision"]:
        raise ValueError("BART-base snapshot revision differs from protocol")
    purpose = "Person 4 BART-base training on shared BFCL data" if protocol else "Synthetic local engineering smoke"
    report_scope = ("BFCL 开发集文本恢复。按已见措辞的损失选择模型，词句与功能保留独立审核。"
                    if protocol else "人工样本工程试跑。字面约束检查需要结合功能保留审核。")
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    start = time.perf_counter()
    try:
        random.seed(args.seed)
        np.random.seed(args.seed)
        torch.manual_seed(args.seed)
        if device == "mps":
            torch.mps.manual_seed(args.seed)
        torch.set_num_threads(4)
        config = {k: str(v.resolve()) if isinstance(v, Path) else v for k, v in vars(args).items() if k != "command"}
        config.update(device=device, model_path=str(source), dtype="float32", attention="eager",
                      train_sha256=sha256(args.train), dev_sha256=sha256(args.dev),
                      actual_effective_batch=args.batch_size * args.accumulation_steps,
                      loss_reduction="Mean over valid target tokens; accumulation weighted by non-padding target-token counts",
                      selection_rule=protocol["selection"] if protocol else "Highest synthetic-dev exact-match rate; earliest tie",
                      generation=protocol["generation"] if protocol else "Greedy with a fixed generation limit",
                      purpose=purpose,
                      source_code_sha256={p.name: sha256(p) for p in HERE.glob("*.py")})
        if protocol:
            config.update(protocol_id=protocol["protocol_id"], protocol_sha256=sha256(args.protocol),
                          data_manifest_sha256=protocol["shared_data_manifest_sha256"],
                          selection_dev_examples=len(selection_dev), selection_excluded_variant=protocol["excluded_selection_variant"])
            write_json(out / "protocol.json", protocol)
        if (HERE / "model_source.json").exists() and source == model_path(None):
            config["pretrained_source"] = json.loads((HERE / "model_source.json").read_text())
        write_json(out / "run_config.json", config)
        write_json(out / "environment.json", environment())
        write_json(out / "data_validation.json", split_info)
        tokenizer, model = load_model(source, device)
        config["effective_generation_config"] = model.generation_config.to_dict()
        config["generation_ceiling"] = args.max_new_tokens
        write_json(out / "run_config.json", config)
        if args.max_input_tokens > model.config.max_position_embeddings or args.max_target_tokens > model.config.max_position_embeddings:
            raise ValueError("Configured training length exceeds model context")
        for split, rows in [("train", pairs_train), ("dev", pairs_dev)]:
            for row in rows:
                n_input = len(tokenizer(args.prefix + row["input_description"], truncation=False)["input_ids"])
                n_target = len(tokenizer(row["target_description"], truncation=False)["input_ids"])
                if n_input > args.max_input_tokens or n_target > args.max_target_tokens:
                    raise ValueError(f"{split}/{row['example_id']}: configured limits would truncate input/target ({n_input}/{n_target}); no truncation performed")
        inputs_dev = inference_rows(pairs_dev)
        decode = dict(device=device, batch_size=args.batch_size, prefix=args.prefix,
                      max_input_tokens=args.max_input_tokens, max_new_tokens=args.max_new_tokens,
                      input_based_limit=bool(protocol))
        before = generate(model, tokenizer, inputs_dev, run_id=out.name + "-pretrained", **decode)
        write_jsonl(out / "pretrained_rewrites.jsonl", before)
        initial_metrics, initial_details = audit(inputs_dev, before, pairs_dev)
        save_report(out / "pretrained_audit", initial_metrics, initial_details, "BART 未微调开发集改写", report_scope)
        optimizer = torch.optim.AdamW(model.parameters(), lr=args.learning_rate, weight_decay=0.01)
        history, best_epoch, best_score, stale, updates = [], 0, float("-inf"), 0, 0
        peak = memory(device)
        selected_outputs = None

        def sample_memory():
            for key, value in memory(device).items():
                peak[key] = max(peak.get(key, 0), value)

        def batch(rows):
            encoded = tokenizer([args.prefix + r["input_description"] for r in rows], padding=True, truncation=False, return_tensors="pt")
            labels = tokenizer([r["target_description"] for r in rows], padding=True, truncation=False, return_tensors="pt")["input_ids"]
            labels[labels == tokenizer.pad_token_id] = -100
            return encoded.to(device), labels.to(device)

        for epoch in range(1, args.epochs + 1):
            epoch_start = time.perf_counter()
            model.train()
            order = list(pairs_train)
            random.Random(args.seed + epoch).shuffle(order)
            train_total, train_tokens = 0.0, 0
            effective = args.batch_size * args.accumulation_steps
            for offset in range(0, len(order), effective):
                group = order[offset:offset + effective]
                denominator = sum(len(tokenizer(r["target_description"])["input_ids"]) for r in group)
                optimizer.zero_grad(set_to_none=True)
                for i in range(0, len(group), args.batch_size):
                    encoded, labels = batch(group[i:i + args.batch_size])
                    count = int((labels != -100).sum().item())
                    loss = model(**encoded, labels=labels, use_cache=False).loss
                    if not torch.isfinite(loss).item():
                        raise RuntimeError("Nonfinite training loss")
                    (loss * count / denominator).backward()
                    train_total += float(loss.detach().cpu()) * count
                    train_tokens += count
                    sample_memory()
                norm = torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                if not torch.isfinite(norm).item():
                    raise RuntimeError("Nonfinite gradient norm")
                optimizer.step()
                updates += 1
            model.eval()
            dev_total, dev_tokens, dev_batch_losses = 0.0, 0, []
            with torch.inference_mode():
                for offset in range(0, len(selection_dev), args.batch_size):
                    encoded, labels = batch(selection_dev[offset:offset + args.batch_size])
                    count = int((labels != -100).sum().item())
                    loss = model(**encoded, labels=labels, use_cache=False).loss
                    if not torch.isfinite(loss).item():
                        raise RuntimeError("Nonfinite dev loss")
                    value = float(loss.cpu())
                    dev_batch_losses.append(value)
                    dev_total += value * count
                    dev_tokens += count
            outputs = generate(model, tokenizer, inputs_dev, run_id=out.name, **decode)
            scores, _ = audit(inputs_dev, outputs, pairs_dev)
            sample_memory()
            sync(device)
            row = {"epoch": epoch, "optimizer_updates": updates, "train_token_nll": train_total / train_tokens,
                   "dev_token_nll": dev_total / dev_tokens, "dev_exact_match_rate": scores["exact_match_rate"],
                   "selection_dev_mean_batch_loss": sum(dev_batch_losses) / len(dev_batch_losses),
                   "dev_protected_span_pass_rate": scores["protected_span_pass_rate"],
                   "dev_error_n": scores["error_or_missing_n"], "seconds": round(time.perf_counter() - epoch_start, 3)}
            history.append(row)
            write_jsonl(out / "history.jsonl", history)
            print(json.dumps(row), flush=True)
            score = -row["selection_dev_mean_batch_loss"] if protocol else scores["exact_match_rate"]
            if score > best_score:
                best_score, best_epoch, stale = score, epoch, 0
                model.save_pretrained(out / "checkpoint", safe_serialization=True)
                tokenizer.save_pretrained(out / "checkpoint")
                selected_outputs = outputs
                write_jsonl(out / "selected_dev_rewrites.jsonl", outputs)
            else:
                stale += 1
            if stale >= args.patience:
                print(f"Early stopping after {stale} epochs without selection-score improvement", flush=True)
                break
        del optimizer, model
        release(device)
        tokenizer, reloaded = load_model(out / "checkpoint", device)
        outputs = generate(reloaded, tokenizer, inputs_dev, run_id=out.name, **decode)
        write_jsonl(out / "rewrites.jsonl", outputs)
        fields = ("description_id", "normalized_description", "status", "truncated")
        differences = [a["description_id"] for a, b in zip(selected_outputs, outputs) if any(a[k] != b[k] for k in fields)]
        reload_check = {"checkpoint_loaded": True, "n_compared": len(outputs), "different_ids": differences,
                        "passed": not differences, "decoding": "Greedy, same inputs/settings/device"}
        write_json(out / "reload_check.json", reload_check)
        metrics, details = audit(inputs_dev, outputs, pairs_dev)
        save_report(out, metrics, details, "BART 开发集改写", report_scope)
        train_metrics = None
        if not protocol:
            train_outputs = generate(reloaded, tokenizer, inference_rows(pairs_train), run_id=out.name, **decode)
            write_jsonl(out / "train_rewrites.jsonl", train_outputs)
            train_metrics, train_details = audit(inference_rows(pairs_train), train_outputs, pairs_train)
            save_report(out / "train_audit", train_metrics, train_details, "BART 人工训练样本改写")
        sample_memory()
        summary = {"status": "complete", "purpose": purpose, "device": device,
                   "best_epoch": best_epoch, "epochs_completed": len(history), "optimizer_updates": updates,
                   "wall_seconds": round(time.perf_counter() - start, 3),
                   "peak_observed_memory_bytes": peak,
                   "memory_measurement_note": "Sampled process RSS and device allocator counters, not a continuous system-wide peak",
                   "pretrained_dev_metrics": initial_metrics, "reloaded_dev_metrics": metrics,
                   "train_metrics": train_metrics, "reload_check": reload_check,
                   "shared_bfcl_training_performed": bool(protocol), "held_out_inputs_used_for_checkpoint_selection": False}
        write_json(out / "summary.json", summary)
        plot_history(history, out, bool(protocol))
        write_json(out / "run_status.json", {"status": "complete", "reload_check_passed": reload_check["passed"]})
        print(json.dumps({k: summary[k] for k in ("status", "device", "best_epoch", "wall_seconds")}), flush=True)
        return summary
    except BaseException as exc:
        write_json(out / "run_status.json", {"status": "failed", "exception": type(exc).__name__, "error": str(exc),
                                            "wall_seconds": round(time.perf_counter() - start, 3)})
        raise
