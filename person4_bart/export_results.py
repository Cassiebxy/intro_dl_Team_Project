"""Export a lightweight, machine-independent result bundle from a completed local run."""
from __future__ import annotations

import argparse
import csv
import json
import os
import shutil
import zipfile
from pathlib import Path

from .core import read_jsonl, sha256, write_json, write_jsonl
from .generalization import PACKAGE, PROTOCOL

HERE = Path(__file__).resolve().parent
CUES = [
    ("table3_cue_1", "Seen priority"),
    ("person4_wording_01", "Priority wording 1"),
    ("person4_wording_03", "Priority wording 2"),
    ("person4_maintenance_02", "Maintenance"),
    ("person4_social_02", "Social proof"),
]


def plot_rewrites(out: Path, text_summary):
    os.environ["MPLCONFIGDIR"] = str(HERE / ".cache/matplotlib")
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    by_variant = {r["label"]: r for r in text_summary["generalization"] if r["axis"] == "variant"}
    cases = [("clean", "Clean"), *CUES]
    numbers = [by_variant[cue] for cue, _ in cases]
    fig, ax = plt.subplots(figsize=(8.4, 4.3))
    bars = ax.barh([label for _, label in cases], [100 * r["exact_rate"] for r in numbers],
                   color=["#8a9bab", "#456582", "#266659", "#266659", "#aa6b34", "#aa6b34"])
    ax.invert_yaxis()
    ax.bar_label(bars, labels=[f"{r['exact_n']}/{r['pairs']}" for r in numbers], padding=5)
    ax.set(xlim=(0, 112), xticks=range(0, 101, 20), xlabel="Exact description recovery (%)",
           title="BART-base on 19 held-out BFCL tool descriptions")
    ax.set_axisbelow(True)
    ax.grid(axis="x", alpha=0.2)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(out / "rewrites_by_cue.png", dpi=180)
    plt.close(fig)


def plot_selection(out: Path):
    import matplotlib.pyplot as plt

    with (out / "mlx-groups/paired_summary.csv").open(encoding="utf-8", newline="") as stream:
        rows = {r["label"]: r for r in csv.DictReader(stream) if r["axis"] == "cue"}
    x = list(range(len(CUES)))
    raw, normalized, rec = [], [], []
    for cue_id, _ in CUES:
        row = rows[cue_id]
        raw.append(100 * float(row["mean_absolute_stratum_raw_minus_clean_sr_b"]))
        normalized.append(100 * float(row["mean_absolute_stratum_norm_minus_clean_sr_b"]))
        rec.append(100 * float(row["norm_minus_raw_rec"]))
    fig, (choice, correctness) = plt.subplots(1, 2, figsize=(11.7, 4.8), sharex=True)
    choice.bar([v - 0.18 for v in x], raw, width=0.34, label="Manipulated", color="#aa6b34")
    choice.bar([v + 0.18 for v in x], normalized, width=0.34, label="BART normalized", color="#266659")
    choice.set(ylabel="Mean absolute gap to clean (pp)", title="Edited-tool selection rate")
    choice.legend(frameon=False)
    correctness.bar(x, rec, width=0.51, color="#456582")
    correctness.axhline(0, color="#59646f", linewidth=0.8)
    correctness.set(ylabel="Normalized minus manipulated (pp)", title="Strict tool-call correctness")
    labels = ["Seen\npriority", "Priority\nwording 1", "Priority\nwording 2", "Maintenance", "Social\nproof"]
    for ax in (choice, correctness):
        ax.set_xticks(x, labels)
        ax.set_axisbelow(True)
        ax.grid(axis="y", alpha=0.2)
        ax.spines[["top", "right"]].set_visible(False)
    fig.suptitle("Matched Qwen2.5-7B MLX 4-bit results on 13 held-out tool groups", fontsize=13)
    fig.tight_layout()
    fig.savefig(out / "qwen_mlx_by_cue.png", dpi=180)
    plt.close(fig)


def export(run: Path, output: Path):
    train = json.loads((run / "summary.json").read_text(encoding="utf-8"))
    if train["status"] != "complete" or not train["reload_check"]["passed"]:
        raise ValueError("Export requires a verified training checkpoint")
    text_eval, qwen = run / "text_evaluation", run / "qwen"
    text_summary = json.loads((text_eval / "rewrite_summary.json").read_text(encoding="utf-8"))
    local_status = json.loads((qwen / "mlx-groups/run_status.json").read_text(encoding="utf-8"))
    if local_status["status"] != "complete":
        raise ValueError("Export requires completed local Qwen scoring")

    output.mkdir(parents=True, exist_ok=False)
    for filename, source in [("training_history.jsonl", run / "history.jsonl"), ("training_curves.png", run / "training_curves.png"),
                             ("dev_rewrites.jsonl", run / "rewrites.jsonl"),
                             ("person2_test_rewrites.jsonl", text_eval / "person2_test/rewrites.jsonl"),
                             ("generalization_rewrites.jsonl", text_eval / "generalization/rewrites.jsonl"),
                             ("rewrite_summary.csv", text_eval / "rewrite_summary.csv"),
                             ("paired_dev_vs_flan.csv", text_eval / "paired_dev_vs_flan.csv")]:
        shutil.copyfile(source, output / filename)
    for backend in ("autodl-replay", "mlx-groups"):
        destination = output / backend
        destination.mkdir()
        source = qwen / f"{backend}_scores"
        for filename in ("condition_summary.csv", "paired_summary.csv", "coverage.csv", "rewrite_vs_call.csv", "summary.json"):
            shutil.copyfile(source / filename, destination / filename)
    for filename in ("raw_unique.jsonl", "run_manifest.json", "run_status.json"):
        shutil.copyfile(qwen / "mlx-groups" / filename, output / "mlx-groups" / filename)
    shutil.copyfile(qwen / "manifest.json", output / "qwen_matrix.json")

    misses = []
    for label, path in [("dev", run / "case_audit.jsonl"), ("generalization", text_eval / "generalization/case_audit.jsonl")]:
        for row in read_jsonl(path):
            if row["exact_match"] is False:
                copied = row["normalized_description"] == row["input_description"]
                misses.append({"dataset": label, **row, "text_difference": "copied_input" if copied else "modified_text"})
    write_jsonl(output / "rewrite_mismatches.jsonl", misses)
    config = json.loads((run / "run_config.json").read_text(encoding="utf-8"))
    runtime = json.loads((run / "environment.json").read_text(encoding="utf-8"))
    write_json(output / "bart_run.json", {
        "run_id": run.name, "model_id": config["pretrained_source"]["model_id"], "revision": config["pretrained_source"]["revision"],
        "training": {k: config[k] for k in ("seed", "device", "dtype", "attention", "epochs", "batch_size", "accumulation_steps",
                                             "learning_rate", "selection_rule", "generation", "train_sha256", "dev_sha256",
                                             "protocol_sha256", "data_manifest_sha256", "source_code_sha256", "loss_reduction")},
        "environment": {k: runtime[k] for k in ("platform", "hardware", "packages")},
        "selected_checkpoint": json.loads((text_eval / "checkpoint_selection.json").read_text(encoding="utf-8")),
        "training_summary": train,
    })
    plot_rewrites(output, text_summary)
    plot_selection(output)

    pending = qwen / "autodl_pending_requests.zip"
    if not pending.exists():
        with zipfile.ZipFile(pending, "x", compression=zipfile.ZIP_DEFLATED) as package:
            for name in ("manifest.json", "autodl_pending_inputs.jsonl", "autodl_pending_mapping.jsonl"):
                package.write(qwen / name, arcname=name)
    shutil.copyfile(pending, output / pending.name)
    write_json(output / "manifest.json", {
        "run_id": run.name, "protocol_sha256": sha256(PROTOCOL), "test_manifest_sha256": sha256(PACKAGE / "manifest.json"),
        "autodl_pending_archive_sha256": sha256(pending),
        "files": {p.relative_to(output).as_posix(): sha256(p) for p in sorted(output.rglob("*")) if p.is_file()},
    })


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    export(args.run.resolve(), args.output.resolve())
