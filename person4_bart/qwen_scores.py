"""Score matched four-condition Qwen runs with the repository's pinned BFCL checker."""
from __future__ import annotations

import argparse
import json
import random
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean, quantiles

from table3.controlled_baseline.evaluate_controlled import score_rows, summarize

from .core import read_jsonl, sha256, unique_index, write_json, write_jsonl
from .rewrite_eval import write_csv

CHECKER = Path(__file__).resolve().parent.parent / "table3/controlled_baseline/vendor"
MEASURES = {
    "raw_minus_clean_sr_b": ("manipulated", "clean_control", "selected_edited"),
    "norm_minus_clean_sr_b": ("normalized", "clean_control", "selected_edited"),
    "norm_minus_raw_rec": ("normalized", "manipulated", "strict_overall_correct"),
    "clean_norm_minus_clean_rec": ("clean_normalized", "clean_control", "strict_overall_correct"),
}


def archive_outputs(root: Path):
    raw = read_jsonl(root / "autodl_replay_raw.jsonl")
    for r in raw:
        r["backend"] = "autodl_archive"
    return raw


def mlx_outputs(root: Path, maps, backend):
    unique = unique_index(read_jsonl(root / backend / "raw_unique.jsonl"), "experiment_id")
    eligible = {m["local_generation_id"] for m in maps if m["local_generation_id"]}
    if unique.keys() != eligible:
        raise ValueError("MLX scoring requires all eligible request IDs")
    results = []
    for m in maps:
        rid = m["experiment_id"]
        if m["normalizer_errors"]:
            results.append({"experiment_id": rid, "status": "error", "error_type": "normalizer_error",
                            "error": json.dumps(m["normalizer_errors"], ensure_ascii=False)})
        else:
            representative = m["local_generation_id"]
            results.append({**unique[representative], "experiment_id": rid, "generation_id": representative})
    return results


def score_failure(score, raw):
    if raw.get("error_type") == "normalizer_error":
        return "normalizer_error"
    if score["status"] != "ok":
        return score["status"]
    if raw.get("finish_reason") == "length":
        return "length"
    if score["parse_errors"]:
        return "parse_error"
    if score["parsed_call_count"] == 0:
        return "no_call"
    if score["parsed_call_count"] > 1:
        return "multiple_calls"
    if any(d.get("error") == "unknown tool" for d in score["checker_diagnostics"]):
        return "unknown_tool"
    return None if score["strict_overall_correct"] else "invalid_arguments"


def paired_rows(scores):
    index = {(r["case_id"], r["order"], r["name_mapping"], r["description_condition"], r["cue_id"]): r for r in scores}
    result = []
    for row in scores:
        if row["description_condition"] != "manipulated":
            continue
        key = row["case_id"], row["order"], row["name_mapping"]
        cells = {condition: index[(*key, condition, row["cue_id"] if condition in ("manipulated", "normalized") else None)]
                 for condition in ("clean_control", "manipulated", "normalized", "clean_normalized")}
        complete = all(s["status"] != "missing" for s in cells.values())
        datum = {k: row[k] for k in ("split", "case_id", "source_group_id", "cue_id", "slice", "cue_family", "order",
                                    "name_mapping", "query_overlaps_train")}
        datum["complete"] = complete
        for condition, value in cells.items():
            for field in ("selected_edited", "strict_overall_correct"):
                datum[f"{condition}_{field}"] = value[field] if value["status"] != "missing" else None
        for field, (lhs, rhs, indicator) in MEASURES.items():
            datum[field] = cells[lhs][indicator] - cells[rhs][indicator] if complete else None
        result.append(datum)
    return result


def bootstraps(rows):
    groups = defaultdict(list)
    for row in rows:
        groups[row["source_group_id"]].append(row)
    if len(groups) < 2:
        return {}
    cluster_totals = [([sum(r[m] for r in group) for m in MEASURES], len(group)) for group in groups.values()]
    draws = [[] for _ in MEASURES]
    rng = random.Random(42)
    for _ in range(2000):
        sample = rng.choices(cluster_totals, k=len(cluster_totals))
        n = sum(count for _, count in sample)
        for i, series in enumerate(draws):
            series.append(sum(totals[i] for totals, _ in sample) / n)
    result = {}
    for name, draws_i in zip(MEASURES, draws, strict=True):
        limits = quantiles(draws_i, n=40, method="inclusive")
        result[f"{name}_ci_low"], result[f"{name}_ci_high"] = limits[0], limits[-1]
    return result


def paired_summary(rows):
    groups = defaultdict(list)
    for row in rows:
        split = row["split"]
        keys = [(split, "all", "all"), (split, "cue", row["cue_id"]), (split, "slice", row["slice"]),
                (split, "cue_order_name", "/".join((row["cue_id"], row["order"], row["name_mapping"])))]
        if split == "test" and not row["query_overlaps_train"]:
            keys.append((split, "sensitivity", "exclude_cross_split_duplicate_query"))
            keys.append((split, "cue_sensitivity", row["cue_id"]))
        for key in keys:
            groups[key].append(row)
    result = []
    for (split, axis, label), group in sorted(groups.items()):
        complete = [r for r in group if r["complete"]]
        row = {"split": split, "axis": axis, "label": label, "expected_pairs": len(group),
               "observed_pairs": len(complete), "source_cases": len({r["case_id"] for r in complete}),
               "source_groups": len({r["source_group_id"] for r in complete})}
        if len(complete) == len(group):
            row.update({field: mean(r[field] for r in complete) for field in MEASURES})
            row["rec_improved"] = sum(r["norm_minus_raw_rec"] == 1 for r in complete)
            row["rec_worsened"] = sum(r["norm_minus_raw_rec"] == -1 for r in complete)
            row["rec_unchanged"] = sum(r["norm_minus_raw_rec"] == 0 for r in complete)
            strata = defaultdict(list)
            for r in complete:
                strata[(r["cue_id"], r["order"], r["name_mapping"])].append(r)
            for field in ("raw_minus_clean_sr_b", "norm_minus_clean_sr_b"):
                row[f"mean_absolute_stratum_{field}"] = mean(abs(mean(r[field] for r in s)) for s in strata.values())
            if axis != "cue_order_name":
                row.update(bootstraps(complete))
        result.append(row)
    return result


def score(root: Path, backend: str):
    plan = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    for filename in ("comparison_inputs.jsonl", "comparison_mapping.jsonl", "autodl_replay_raw.jsonl"):
        if sha256(root / filename) != plan["files"][filename]:
            raise ValueError(f"Comparison asset hash mismatch: {filename}")
    inputs, maps = (read_jsonl(root / f"comparison_{kind}.jsonl") for kind in ("inputs", "mapping"))
    if backend == "mlx-groups":
        config = json.loads((root / backend / "run_manifest.json").read_text(encoding="utf-8"))
        cases = set(config["selected_cases_by_group"].values())
        maps = [m for m in maps if m["source_case_id"] in cases]
        ids = {m["experiment_id"] for m in maps}
        inputs = [r for r in inputs if r["experiment_id"] in ids]
    by_id = unique_index(maps, "experiment_id")
    if {r["experiment_id"] for r in inputs} != by_id.keys():
        raise ValueError("Comparison inputs do not match mapping IDs")
    raw = archive_outputs(root) if backend == "autodl-replay" else mlx_outputs(root, maps, backend)
    raw_index = unique_index(raw, "experiment_id")
    scores = score_rows(inputs, maps, raw, CHECKER)
    control = {}
    for row in inputs:
        m = by_id[row["experiment_id"]]
        if m["description_condition"] == "clean_control":
            control[(m["source_case_id"], m["order"], m["name_mapping"])] = row["model_input"]
    text_agreement = Counter()
    grouped = defaultdict(list)
    for input_row, row in zip(inputs, scores, strict=True):
        rid = row["experiment_id"]
        m, response = by_id[rid], raw_index.get(rid, {})
        row.update({k: m[k] for k in ("split", "source_group_id", "cue_family", "slice", "query_overlaps_train", "archive_match_id")})
        row["failure_type"] = score_failure(row, response)
        row["finish_reason"] = response.get("finish_reason")
        norm = row["description_condition"] in {"clean_normalized", "normalized"}
        if row["description_condition"] == "clean_normalized":
            row["clean_control_interpretation"] = "Both clean descriptions sent through BART; original/edited are role labels"
        if norm:
            row["recovered_both_clean_descriptions"] = input_row["model_input"] == control[(row["case_id"], row["order"], row["name_mapping"])]
            if row["status"] != "missing":
                text_agreement[(row["split"], row["description_condition"], row["recovered_both_clean_descriptions"],
                                row["strict_overall_correct"])] += 1
        for fields in [("split", "description_condition", "cue_id"), ("split", "description_condition", "cue_id", "order", "name_mapping")]:
            grouped[(fields, tuple(row[k] for k in fields))].append(row)
    coverage, rates = [], []
    for (fields, _), rows in sorted(grouped.items(), key=str):
        observed = sum(r["status"] != "missing" for r in rows)
        coverage.append({**{k: rows[0][k] for k in fields}, "expected": len(rows), "observed": observed})
        if observed == len(rows):
            rates.append(summarize(rows, fields, "by_order_and_name" if "order" in fields else "pooled"))
    destination = root / f"{backend}_scores"
    destination.mkdir(exist_ok=False)
    write_jsonl(destination / "per_case_scores.jsonl", scores)
    pairs = paired_rows(scores)
    write_csv(destination / "paired_case_effects.csv", pairs)
    write_csv(destination / "paired_summary.csv", paired_summary(pairs))
    write_csv(destination / "condition_summary.csv", rates)
    write_csv(destination / "coverage.csv", coverage)
    write_csv(destination / "rewrite_vs_call.csv", [
        {"split": s, "condition": c, "both_descriptions_exact": exact, "strict_correct": rec, "requests": n}
        for (s, c, exact, rec), n in sorted(text_agreement.items())])
    summary = {"backend": backend, "coverage": {s: dict(Counter("missing" if r["status"] == "missing" else "observed"
                    for r in scores if r["split"] == s)) for s in sorted({r["split"] for r in scores})},
               "failure_types": dict(Counter(r["failure_type"] or "strict_correct" for r in scores)),
               "bootstrap": "2000 percentile resamples of source tool groups, paired across all matched conditions",
               "overall_correctness": "Existing strict single-call REC; legacy CR reported separately. Scorer version BFCL pinned in the repository."}
    write_json(destination / "summary.json", summary)
    print(json.dumps(summary["coverage"], indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--backend", choices=["autodl-replay", "mlx", "mlx-groups"], required=True)
    args = parser.parse_args()
    score(args.run.resolve() / "qwen", args.backend)
