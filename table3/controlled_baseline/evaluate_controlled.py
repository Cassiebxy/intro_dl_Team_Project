#!/usr/bin/env python3
"""Score controlled Qwen outputs with the pinned BFCL checker and summarize factors."""
from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
TABLE3 = HERE.parent
sys.path.insert(0, str(HERE))
from core_scoring import score_response  # noqa: E402


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_jsonl(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")


def score_rows(inputs: list[dict], maps: list[dict], raw: list[dict], checker_root: Path) -> list[dict]:
    mapping_by_id = {m["experiment_id"]: m for m in maps}
    raw_by_id = {}
    for r in raw:
        rid = r.get("experiment_id") or r.get("id")
        if rid in raw_by_id:
            raise ValueError(f"Duplicate output ID: {rid}")
        raw_by_id[rid] = r
    if set(raw_by_id) - set(mapping_by_id):
        raise ValueError(f"Unexpected output IDs: {sorted(set(raw_by_id)-set(mapping_by_id))[:5]}")
    result = []
    for row in inputs:
        rid = row["experiment_id"]
        m = mapping_by_id[rid]
        out = raw_by_id.get(rid, {"status": "missing", "raw_text": "", "parsed_calls": [], "parse_errors": []})
        status = out.get("status", "missing")
        parsed = out.get("parsed_calls", []) if status == "ok" else []
        parse_errors = out.get("parse_errors", []) if status == "ok" else []
        calls = []
        for c in parsed:
            name = c.get("canonical_name")
            if name is None:
                name = c.get("wire_name")
            calls.append({name: c.get("arguments", {})})
        score_status = "technical_error" if status in {"error", "missing"} else ("parse_error" if parse_errors else "ok")
        base = {"id": rid, "cue_id": m["cue_id"], "order": m["order"],
                "roles": {role: name for name, role in m["tool_name_to_role"].items()},
                "expected": m["expected"], "function": row["model_input"]["function"]}
        scored = score_response(base, calls, str(checker_root), score_status)
        role_names = base["roles"]
        selected = {role: any(name == role_names[role] for call in calls for name in call) for role in role_names}
        diag_by_name = defaultdict(list)
        for d in scored["diagnostics"]:
            diag_by_name[d.get("name")].append(bool(d.get("valid", False)))
        role_correct = {"original": scored["original_correct"], "edited": scored["edited_correct"]}
        selected_counts = {r: int(selected[r]) for r in ("edited", "original")}
        arg_correct_counts = {r: int(selected[r] and role_correct[r]) for r in ("edited", "original")}
        # Strict single-call correctness for live_simple: exactly one parseable known
        # tool call, exactly one checker diagnostic, and the checker accepts it.
        overall = (status == "ok" and not parse_errors and len(calls) == 1 and
                   len(scored["diagnostics"]) == 1 and scored["cr"] and
                   scored["diagnostics"][0].get("valid") is True and
                   out.get("finish_reason") != "length")
        if m["description_condition"] == "clean_control":
            detail = "clean-control tool_A/tool_B identities; original/edited fields are pseudo-role labels only"
        else:
            detail = "manipulated description condition"
        result.append({
            "experiment_id": rid, "case_id": m["source_case_id"],
            "description_condition": m["description_condition"], "cue_id": m["cue_id"],
            "order": m["order"], "position_by_role": m["position_by_role"],
            "name_mapping": m["name_mapping"], "role_name_suffix": m["role_name_suffix"],
            "seed": out.get("seed"), "status": status, "score_status": score_status,
            "parsed_call_count": len(calls), "parse_errors": parse_errors,
            "selected_edited": selected_counts["edited"], "selected_original": selected_counts["original"],
            "edited_argument_correct": arg_correct_counts["edited"],
            "original_argument_correct": arg_correct_counts["original"],
            "edited_cur_correct": int(scored["edited_correct"]),
            "original_cur_correct": int(scored["original_correct"]),
            "legacy_cr_correct": int(scored["cr"]), "strict_overall_correct": int(overall),
            "calls": calls, "checker_diagnostics": scored["diagnostics"],
            "clean_control_interpretation": detail,
        })
    return result


def summarize(rows: list[dict], group_fields: tuple[str, ...], label: str) -> dict:
    n = len(rows)
    e_sel = sum(r["selected_edited"] for r in rows)
    o_sel = sum(r["selected_original"] for r in rows)
    e_arg = sum(r["edited_argument_correct"] for r in rows)
    o_arg = sum(r["original_argument_correct"] for r in rows)
    e_cur = sum(r["edited_cur_correct"] for r in rows)
    o_cur = sum(r["original_cur_correct"] for r in rows)
    sel_e, sel_o = e_sel / n if n else None, o_sel / n if n else None
    return {
        "aggregation": label,
        **{k: rows[0][k] for k in group_fields},
        "n_requests": n,
        "completed": sum(r["status"] == "ok" for r in rows),
        "missing_or_technical": sum(r["status"] in {"missing", "error"} for r in rows),
        "parse_failures": sum(r["score_status"] == "parse_error" for r in rows),
        "edited_selected_n": e_sel, "edited_selection_rate": sel_e,
        "original_selected_n": o_sel, "original_selection_rate": sel_o,
        "selection_ratio_edited_over_original": sel_e / sel_o if sel_o else None,
        "edited_arg_correct_n_given_selected": e_arg,
        "edited_argument_accuracy_conditional": e_arg / e_sel if e_sel else None,
        "original_arg_correct_n_given_selected": o_arg,
        "original_argument_accuracy_conditional": o_arg / o_sel if o_sel else None,
        "edited_cur_correct_n": e_cur, "edited_cur": e_cur / n if n else None,
        "original_cur_correct_n": o_cur, "original_cur": o_cur / n if n else None,
        "legacy_cr_correct_n": sum(r["legacy_cr_correct"] for r in rows),
        "legacy_cr": sum(r["legacy_cr_correct"] for r in rows) / n if n else None,
        "strict_overall_correct_n": sum(r["strict_overall_correct"] for r in rows),
        "strict_overall_correctness": sum(r["strict_overall_correct"] for r in rows) / n if n else None,
    }


def paired_contrasts(rows: list[dict]) -> list[dict]:
    """Case-paired contrasts that isolate one crossed design factor at a time."""
    index = {}
    for r in rows:
        key = (r["case_id"], r["description_condition"], r["cue_id"], r["order"], r["name_mapping"])
        index[key] = r
    measures = ("selected_edited", "selected_original", "edited_cur_correct",
                "original_cur_correct", "legacy_cr_correct", "strict_overall_correct")
    contrasts = []

    def emit(kind: str, factor: dict, a: dict, b: dict, label_a: str, label_b: str) -> None:
        deltas = {m: b[m] - a[m] for m in measures}
        contrasts.append({"contrast": kind, **factor, "from_level": label_a, "to_level": label_b,
                          "n_paired_cases": len(deltas) and 1,
                          **{f"delta_{m}": v for m, v in deltas.items()}})

    # Description effect: manipulated cue vs clean, at fixed order and name assignment.
    for r in rows:
        if r["description_condition"] == "clean_control":
            continue
        clean_key = (r["case_id"], "clean_control", None, r["order"], r["name_mapping"])
        clean = index.get(clean_key)
        if clean:
            emit("description_vs_clean", {"case_id": r["case_id"], "cue_id": r["cue_id"],
                 "order": r["order"], "name_mapping": r["name_mapping"]},
                 clean, r, "clean_control", r["description_condition"])
    # Position effect: original/edited role first vs second, at fixed description and names.
    for r in rows:
        if r["order"] != "edited_first":
            continue
        key = (r["case_id"], r["description_condition"], r["cue_id"], "original_first", r["name_mapping"])
        other = index.get(key)
        if other:
            emit("position_role_first_vs_second", {"case_id": r["case_id"],
                 "description_condition": r["description_condition"], "cue_id": r["cue_id"],
                 "name_mapping": r["name_mapping"]}, other, r, "edited/original_role_first", "edited/original_role_second")
    # Naming effect: edited/original roles receive suffixes 1/2 vs 2/1, at fixed order/content.
    for r in rows:
        if r["name_mapping"] != "edited_suffix1":
            continue
        key = (r["case_id"], r["description_condition"], r["cue_id"], r["order"], "original_suffix1")
        other = index.get(key)
        if other:
            emit("name_mapping", {"case_id": r["case_id"], "description_condition": r["description_condition"],
                 "cue_id": r["cue_id"], "order": r["order"]}, other, r,
                 "original_suffix1", "edited_suffix1")
    # Collapse per-case binary differences into transparent means/counts.
    grouped = defaultdict(list)
    for row in contrasts:
        key = tuple((k, row.get(k)) for k in ("contrast", "cue_id", "description_condition", "order", "name_mapping", "from_level", "to_level") if k != "case_id")
        grouped[key].append(row)
    out = []
    for key, group in sorted(grouped.items(), key=lambda item: str(item[0])):
        first = {k: v for k, v in key}
        first["n_paired_cases"] = len(group)
        for metric in measures:
            vals = [r[f"delta_{metric}"] for r in group]
            first[f"delta_{metric}_mean"] = sum(vals) / len(vals)
            first[f"delta_{metric}_positive_n"] = sum(v > 0 for v in vals)
            first[f"delta_{metric}_negative_n"] = sum(v < 0 for v in vals)
        out.append(first)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input", type=Path, default=HERE / "generated" / "controlled_inputs.jsonl")
    ap.add_argument("--mapping", type=Path, default=HERE / "generated" / "controlled_mapping.jsonl")
    ap.add_argument("--responses", type=Path, required=True)
    ap.add_argument("--checker-root", type=Path, default=HERE / "vendor")
    ap.add_argument("--output-dir", type=Path, required=True)
    args = ap.parse_args()
    inputs, maps, raw = read_jsonl(args.input), read_jsonl(args.mapping), read_jsonl(args.responses)
    if not args.checker_root.joinpath("bfcl").is_dir():
        raise FileNotFoundError(f"Pinned BFCL checker tree missing under {args.checker_root}")
    per_case = score_rows(inputs, maps, raw, args.checker_root)
    args.output_dir.mkdir(parents=True, exist_ok=False)
    write_jsonl(args.output_dir / "per_case_structured_results.jsonl", per_case)
    factors = [
        (("description_condition", "cue_id", "order", "name_mapping"), "condition_cell"),
        (("description_condition", "cue_id", "order"), "description_by_order"),
        (("description_condition", "cue_id", "name_mapping"), "description_by_name_mapping"),
        (("description_condition", "cue_id"), "description_marginal"),
        (("order",), "position_marginal"),
        (("name_mapping",), "name_mapping_marginal"),
    ]
    summaries = []
    for fields, label in factors:
        groups = defaultdict(list)
        for r in per_case:
            key = tuple(r[k] for k in fields)
            groups[key].append(r)
        summaries.extend(summarize(v, fields, label) for _, v in sorted(groups.items(), key=lambda kv: str(kv[0])))
    contrasts = paired_contrasts(per_case)
    if summaries:
        with (args.output_dir / "summary_by_condition.csv").open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(dict.fromkeys(k for r in summaries for k in r)))
            writer.writeheader()
            writer.writerows(summaries)
        (args.output_dir / "summary_by_condition.json").write_text(json.dumps(summaries, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (args.output_dir / "paired_factor_contrasts.json").write_text(json.dumps(contrasts, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if contrasts:
        with (args.output_dir / "paired_factor_contrasts.csv").open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(dict.fromkeys(k for r in contrasts for k in r)))
            writer.writeheader()
            writer.writerows(contrasts)
    status = {"expected_requests": len(inputs), "observed_responses": len(raw),
              "complete": len(raw) == len(inputs), "scored_rows": len(per_case),
              "overall_correctness_convention": "strict single-call live_simple convention; pending team/TA confirmation"}
    (args.output_dir / "evaluation_status.json").write_text(json.dumps(status, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(status, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
