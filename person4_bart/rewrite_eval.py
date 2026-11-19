"""Evaluate the selected BART checkpoint on the two held-out text datasets."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path

from .core import audit, inference_rows, load_inputs, load_pairs, read_jsonl, save_report, sha256, unique_index, write_json, write_jsonl
from .generalization import PACKAGE, PROTOCOL, shared_data
from .model import device_for, generate, load_model


def write_csv(path, rows):
    fields = list(dict.fromkeys(key for row in rows for key in row))
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def group_summary(pairs, details):
    by_id = unique_index(details, "description_id")
    groups = defaultdict(list)
    for pair in pairs:
        groups[("total", "all")].append(pair)
        groups[("variant", pair["variant"])].append(pair)
        if "slice" in pair:
            groups[("slice", pair["slice"])].append(pair)
    summary = []
    for (axis, label), rows in sorted(groups.items()):
        outcomes = [by_id[r["description_id"]] for r in rows]
        exact = sum(r["exact_match"] for r in outcomes)
        summary.append({"axis": axis, "label": label, "pairs": len(rows),
                        "source_descriptions": len({r["source_tool_id"] for r in rows}),
                        "source_groups": len({r["source_group_id"] for r in rows}),
                        "exact_n": exact, "exact_rate": exact / len(rows),
                        "generation_error_n": sum(r["status"] != "ok" for r in outcomes),
                        "truncated_n": sum(r["truncated"] for r in outcomes)})
    return summary


def main(run: Path, device: str):
    protocol, data = shared_data()
    config = json.loads((run / "run_config.json").read_text(encoding="utf-8"))
    status = json.loads((run / "run_status.json").read_text(encoding="utf-8"))
    manifest = json.loads((PACKAGE / "manifest.json").read_text(encoding="utf-8"))
    if config["protocol_sha256"] != sha256(PROTOCOL) or manifest["protocol_sha256"] != sha256(PROTOCOL):
        raise ValueError("Protocol mismatch between training and held-out inputs")
    if status["status"] != "complete" or not status["reload_check_passed"]:
        raise ValueError("Expected a completed training run with a verified checkpoint reload")
    for filename, digest in manifest["files"].items():
        if sha256(PACKAGE / filename) != digest:
            raise ValueError(f"Held-out package hash mismatch: {filename}")
    output = run / "text_evaluation"
    output.mkdir(exist_ok=False)
    with (run / "checkpoint/model.safetensors").open("rb") as stream:
        checkpoint_hash = hashlib.file_digest(stream, "sha256").hexdigest()
    write_json(output / "checkpoint_selection.json", {
        "checkpoint_sha256": checkpoint_hash,
        "protocol_sha256": config["protocol_sha256"],
        "selection_rule": config["selection_rule"],
        "selection_dev_examples": config["selection_dev_examples"],
        "selected_epoch": json.loads((run / "summary.json").read_text())["best_epoch"],
        "held_out_package_sha256": sha256(PACKAGE / "manifest.json"),
    })
    args = protocol["training"]
    tokenizer, model = load_model(run / "checkpoint", device)
    summaries = {}
    for name, root in [("person2_test", data), ("generalization", PACKAGE)]:
        destination = output / name
        destination.mkdir()
        inputs = load_inputs(root / "normalizer_inputs_test.jsonl")
        pairs = load_pairs(root / "pairs_test.jsonl", "test")
        if inputs != inference_rows(pairs):
            raise ValueError(f"The input-only and scoring files disagree: {name}")
        rows = generate(model, tokenizer, inputs, run_id=run.name, device=device,
                        batch_size=args["batch_size"], prefix=args["prefix"],
                        max_input_tokens=args["max_input_tokens"], max_new_tokens=args["max_new_tokens"],
                        input_based_limit=True)
        write_jsonl(destination / "rewrites.jsonl", rows)
        metrics, details = audit(inputs, rows, pairs)
        if not metrics["contract_valid"]:
            raise ValueError(f"Invalid output coverage: {name}")
        save_report(destination, metrics, details, "BART 留出工具改写",
                    "BFCL 留出工具的文本恢复。Person 2 的 wording probe 在开发集出现过。新泛化包使用另外四条措辞。")
        summaries[name] = group_summary(pairs, details)
        print(name, metrics["exact_match_n"], "/", metrics["n_expected"], flush=True)
    pairs = load_pairs(data / "pairs_dev.jsonl", "dev")
    dev_details = read_jsonl(run / "case_audit.jsonl")
    summaries["person2_dev"] = group_summary(pairs, dev_details)
    flan = unique_index(read_jsonl(data.parent / "small-main-20261118/rewrites.jsonl"), "description_id")
    dev = unique_index(dev_details, "description_id")
    if flan.keys() != dev.keys() or any(flan[rid]["target_description"] != dev[rid]["target_description"] or
                                       flan[rid]["input_description"] != dev[rid]["input_description"] for rid in dev):
        raise ValueError("The published FLAN comparison uses different examples or text")
    comparison = [{"description_id": r["description_id"], "source_group_id": r["source_group_id"],
                   "variant": r["variant"], "bart_exact": dev[r["description_id"]]["exact_match"],
                   "flan_exact": flan[r["description_id"]]["exact"]} for r in pairs]
    write_csv(output / "paired_dev_vs_flan.csv", comparison)
    write_csv(output / "rewrite_summary.csv", [{"dataset": name, **row} for name, rows in summaries.items() for row in rows])
    write_json(output / "rewrite_summary.json", summaries)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--device", choices=["auto", "mps", "cpu", "cuda"], default="auto")
    args = parser.parse_args()
    main(args.run.resolve(), device_for(args.device))
