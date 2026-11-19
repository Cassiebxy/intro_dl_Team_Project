#!/usr/bin/env python3
"""Prepare a 16-request paired check or compare two independent replicates."""
import argparse
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
KNOWN_FAILURES = ["live_simple_188-113-0", "live_simple_67-31-0", "live_simple_70-34-0"]


def read_rows(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def indexed(path):
    rows = read_rows(path)
    result = {row["experiment_id"]: row for row in rows}
    if len(rows) != len(result):
        raise ValueError(f"Duplicate IDs in {path}")
    return result


def prepare(source, destination):
    inputs = indexed(source / "controlled_inputs.jsonl")
    mappings = indexed(source / "controlled_mapping.jsonl")
    if inputs.keys() != mappings.keys():
        raise ValueError("Input/mapping IDs differ")
    available = list(dict.fromkeys(m["source_case_id"] for m in mappings.values()))
    cases = KNOWN_FAILURES + [next(c for c in available if c not in KNOWN_FAILURES)]
    selected = []
    for case in cases:
        for condition in ["clean_control", "table3_cue_1"]:
            for order in ["original_first", "edited_first"]:
                matches = [key for key, m in mappings.items()
                           if (m["source_case_id"], m["description_condition"], m["order"], m["name_mapping"])
                           == (case, condition, order, "original_suffix1")]
                if len(matches) != 1:
                    raise ValueError(f"Missing or duplicate cell for {case}/{condition}/{order}")
                selected.append(matches[0])
        if len({mappings[key]["seed"] for key in selected[-4:]}) != 1:
            raise ValueError("Paired cells must share a seed")
    destination.mkdir(parents=True, exist_ok=False)
    for name, values in [("controlled_inputs.jsonl", inputs), ("controlled_mapping.jsonl", mappings)]:
        (destination / name).write_text("".join(json.dumps(values[key], ensure_ascii=False) + "\n"
                                               for key in selected))
    (destination / "design.json").write_text(json.dumps(
        dict(cases=cases, requests=16, description_conditions=["clean_control", "table3_cue_1"],
             orders=2, name_mapping="original_suffix1", purpose="paired stability check"), indent=2))


def compare(inputs_path, first, second, output):
    expected = indexed(inputs_path)
    raw = [indexed(folder / "raw_responses.jsonl") for folder in [first, second]]
    scored = [indexed(folder / "analysis/per_case_structured_results.jsonl") for folder in [first, second]]
    manifests = [json.loads((folder / "run_manifest.json").read_text()) for folder in [first, second]]
    for key in ["input_sha256", "mapping_sha256", "model_dir", "model_config_sha256",
                "tokenizer_config_sha256", "dtype", "decoding", "max_new_tokens"]:
        if manifests[0].get(key) != manifests[1].get(key):
            raise ValueError(f"Replicate protocol differs at {key}")
    if any(rows.keys() != expected.keys() for rows in raw + scored):
        raise ValueError("Both replicates and evaluations must contain every expected ID exactly once")
    details = []
    for key in expected:
        a, b = raw[0][key], raw[1][key]
        x, y = scored[0][key], scored[1][key]
        healthy = all(r.get("status") == "ok" and not r.get("parse_errors")
                      and r.get("finish_reason") == "stop" for r in [a, b])
        details.append(dict(
            experiment_id=key, both_valid_generations=healthy,
            exact_text_match=a.get("raw_text") == b.get("raw_text"),
            calls_match=x["calls"] == y["calls"],
            selection_match=(x["selected_original"], x["selected_edited"]) ==
                            (y["selected_original"], y["selected_edited"]),
            correctness_match=(x["legacy_cr_correct"], x["strict_overall_correct"]) ==
                              (y["legacy_cr_correct"], y["strict_overall_correct"]),
            output_tokens=[a.get("output_tokens"), b.get("output_tokens")],
            finish_reasons=[a.get("finish_reason"), b.get("finish_reason")]))
    result = dict(requests=len(details),
                  counts={field: sum(r[field] for r in details) for field in
                          ["both_valid_generations", "exact_text_match", "calls_match",
                           "selection_match", "correctness_match"]},
                  interpretation="Review anomalies and differences before expanding; agreement on errors is not successful validation.",
                  details=details)
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result["counts"], indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    prep = sub.add_parser("prepare")
    prep.add_argument("--source", type=Path, default=HERE / "generated/full_factorial_v2")
    prep.add_argument("--output", type=Path, required=True)
    check = sub.add_parser("compare")
    check.add_argument("--input", type=Path, required=True)
    check.add_argument("--first", type=Path, required=True)
    check.add_argument("--second", type=Path, required=True)
    check.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "prepare":
        prepare(args.source, args.output)
    else:
        compare(args.input, args.first, args.second, args.output)
