"""Reproduce three supplemental analyses from Maggie's final 42-case delivery.

Usage: python analyze_final.py final_delivery_BFCL_42case.zip > supplemental_results.json
"""
import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import random
from statistics import mean
from zipfile import ZipFile


SMALL = "FLAN-T5-small A1"
COMPARATORS = ("FLAN-T5-base multi-cue", "BART-base")


def choices(rows, condition):
    out = {}
    for row in rows:
        if row["description_condition"] != condition:
            continue
        key = (row["case_id"], row["order"], row["name_mapping"])
        if condition != "clean_control":
            key += (row["cue_id"],)
        if key in out:
            raise ValueError(f"Duplicate condition: {key}")
        out[key] = (row["selected_original"], row["selected_edited"])
    return out


def recovery(methods):
    clean = choices(methods[SMALL], "clean_control")
    before = choices(methods[SMALL], "manipulated")
    flips = [k for k, value in before.items()
             if sum(value) == sum(clean[k[:3]]) == 1 and value != clean[k[:3]]]
    counts = {}
    for method, rows in methods.items():
        after = choices(rows, "normalized")
        if (choices(rows, "clean_control") != clean or choices(rows, "manipulated") != before
                or after.keys() != before.keys()):
            raise ValueError(f"Unmatched conditions for {method}")
        counts[method] = sum(after[k] == clean[k[:3]] for k in flips)
    return {"paired_conditions": len(before), "eligible_switches": len(flips), "restored": counts}


def clean_failures(rows):
    outcomes = defaultdict(set)
    errors = defaultdict(set)
    for row in rows:
        if row["description_condition"] == "clean_control":
            case = row["case_id"]
            outcomes[case].add(row["legacy_cr_correct"])
            if not row["legacy_cr_correct"]:
                errors[case].update(d["error_type"] for d in row["checker_diagnostics"])
    if any(len(v) != 1 for v in outcomes.values()):
        raise ValueError("Clean pass/fail varies across permutations")
    return {"cases": len(outcomes), "failed_cases": len(errors),
            "checker_categories": Counter(", ".join(sorted(v)) or "no diagnostic" for v in errors.values())}


def paired_gaps(methods):
    counts = Counter()
    correct_diff = Counter()
    for method in (SMALL, *COMPARATORS):
        for row in methods[method]:
            if row["description_condition"] == "normalized":
                key = (method, row["cue_id"], str(row["source_group_id"]))
                counts[key] += 1
                correct_diff[key] += row["edited_cur_correct"] - row["original_cur_correct"]
    cues = sorted({cue for _, cue, _ in counts})
    groups = sorted({group for _, _, group in counts})

    def gap(method, draw):
        return mean(100 * abs(sum(correct_diff[method, cue, g] for g in draw))
                    / sum(counts[method, cue, g] for g in draw) for cue in cues)

    rng = random.Random(42042)
    samples = defaultdict(list)
    for _ in range(2000):
        draw = [rng.choice(groups) for _ in groups]
        small_gap = gap(SMALL, draw)
        for method in COMPARATORS:
            samples[method].append(gap(method, draw) - small_gap)
    comparison = {}
    for method, values in samples.items():
        values.sort()
        comparison[method] = {
            "comparator_minus_small_pp": round(gap(method, groups) - gap(SMALL, groups), 2),
            "percentile_ci95_pp": [round(values[int(p * (len(values) - 1))], 2) for p in (.025, .975)]}
    return comparison


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("delivery", type=Path)
    methods = defaultdict(list)
    with ZipFile(parser.parse_args().delivery) as archive:
        with archive.open("final_delivery_BFCL_42case/results/per_case_bfcl_scores.jsonl") as source:
            for line in source:
                row = json.loads(line)
                methods[row["method"]].append(row)
    print(json.dumps({"choice_recovery": recovery(methods), "clean_failures": clean_failures(methods[SMALL]),
                      "paired_gap_comparison": paired_gaps(methods)}, indent=2))


if __name__ == "__main__":
    main()
