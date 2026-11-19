#!/usr/bin/env python3
"""Generate an isolated 7 x 2 x 2 controlled Qwen Table 3 factorial matrix.

Factors: clean/cue description condition, semantic-role-first order, and which
suffix (1/2) is assigned to each semantic role. Writes only into the selected
new output directory; never changes the historical generated/ files.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import itertools
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
TABLE3 = HERE.parent
BASE_INPUT = TABLE3 / "generated" / "table3_inputs.jsonl"
BASE_MAPPING = TABLE3 / "generated" / "table3_mapping.jsonl"
CUES = TABLE3 / "table3_cues.json"
DEFAULT_OUT = HERE / "generated"
ORDERS = ("original_first", "edited_first")
NAME_MAPS = ("original_suffix1", "edited_suffix1")


def read_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def write_jsonl(path: Path, rows: list[dict]) -> None:
    with path.open("x", encoding="utf-8", newline="\n") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")


def seed_for_case(case_id: str) -> int:
    # Common random number across all 28 cells for a case; deterministic on resume.
    return int(hashlib.sha256(case_id.encode()).hexdigest()[:8], 16) % (2**31)


def generate(base_inputs: list[dict], base_maps: list[dict], cues: list[dict], limit_cases: int | None = None):
    if len(base_inputs) != 3096 or len(base_maps) != 3096:
        raise ValueError("Expected the immutable 3,096-row historical input/mapping tables")
    if len(cues) != 6 or len({c["cue_id"] for c in cues}) != 6:
        raise ValueError("Expected six unique, verified Table 3 cue definitions")
    by_id = {r["experiment_id"]: r for r in base_inputs}
    map_by_id = {r["experiment_id"]: r for r in base_maps}
    if len(by_id) != len(base_inputs) or by_id.keys() != map_by_id.keys():
        raise ValueError("Historical input/mapping IDs are duplicated or mismatched")

    # Extract one clean source function/query and the answer once per canonical case.
    cases = {}
    for request_id, mapping in map_by_id.items():
        if mapping["cue_id"] != "table3_cue_1" or mapping["order"] != "original_first":
            continue
        source_id = mapping["source_case_id"]
        payload = by_id[request_id]["model_input"]
        original_name = mapping["original_function_name"]
        original = next(copy.deepcopy(t) for t in payload["function"] if t["name"] == original_name)
        base_name = mapping["base_function_name"]
        original["name"] = base_name
        # This is an auditable clean description from the historical original role.
        cases[source_id] = {
            "case_id": source_id,
            "question": copy.deepcopy(payload["question"]),
            "base_tool": original,
            "expected_args": copy.deepcopy(mapping.get("expected_args")),
        }
    # Expected argument alternatives are kept out of the model input and copied from
    # the canonical answer file generated alongside the historical inputs.
    answers_path = TABLE3 / "generated" / "table3_answers.jsonl"
    answers = {r["source_case_id"]: r["original_answer"]["ground_truth"]
               for r in read_jsonl(answers_path)}
    for case_id, case in cases.items():
        answer = answers[case_id]
        base_name = case["base_tool"]["name"]
        if len(answer) != 1 or set(answer[0]) != {base_name}:
            raise ValueError(f"Unexpected canonical answer for {case_id}")
        case["expected_args"] = copy.deepcopy(answer[0][base_name])
    case_ids = list(cases)
    if len(case_ids) != 258:
        raise ValueError(f"Expected 258 canonical cases, found {len(case_ids)}")
    if limit_cases is not None:
        if not 1 <= limit_cases <= 258:
            raise ValueError("--limit-cases must be in 1..258")
        case_ids = case_ids[:limit_cases]

    inputs, mappings = [], []
    for case_id in case_ids:
        case = cases[case_id]
        for condition in ("clean", *[c["cue_id"] for c in cues]):
            cue = next((c for c in cues if c["cue_id"] == condition), None)
            for order, name_map in itertools.product(ORDERS, NAME_MAPS):
                # In clean cells, original/edited are only stable identity labels;
                # both descriptions are identical and neither role is manipulated.
                role_suffix = ({"original": "1", "edited": "2"}
                               if name_map == "original_suffix1"
                               else {"original": "2", "edited": "1"})
                role_position = ({"original": 0, "edited": 1}
                                 if order == "original_first"
                                 else {"original": 1, "edited": 0})
                tools_by_role = {}
                for role in ("original", "edited"):
                    tool = copy.deepcopy(case["base_tool"])
                    tool["name"] = tool["name"] + role_suffix[role]
                    if condition != "clean" and role == "edited":
                        tool["description"] = tool["description"] + " " + cue["text"]
                    tools_by_role[role] = tool
                ordered_roles = sorted(role_position, key=role_position.get)
                functions = [tools_by_role[r] for r in ordered_roles]
                roles = {r: tools_by_role[r]["name"] for r in tools_by_role}
                condition_label = "clean_control" if condition == "clean" else condition
                experiment_id = f"controlled::{case_id}::{condition_label}::{order}::{name_map}"
                inputs.append({"experiment_id": experiment_id,
                               "model_input": {"question": copy.deepcopy(case["question"]), "function": functions}})
                mappings.append({
                    "experiment_id": experiment_id,
                    "source_case_id": case_id,
                    "description_condition": condition_label,
                    "cue_id": None if condition == "clean" else cue["cue_id"],
                    "cue_text": None if cue is None else cue["text"],
                    "order": order,
                    "position_by_role": {r: ("first" if role_position[r] == 0 else "second") for r in role_position},
                    "name_mapping": name_map,
                    "role_name_suffix": role_suffix,
                    "tool_name_to_role": {v: k for k, v in roles.items()},
                    "original_function_name": roles["original"],
                    "edited_function_name": roles["edited"],
                    "base_function_name": case["base_tool"]["name"],
                    "expected": [{roles[r]: copy.deepcopy(case["expected_args"])} for r in ("original", "edited")],
                    "seed": seed_for_case(case_id),
                    "seed_policy": "shared SHA256(case_id) seed across all factorial cells for paired case-level decoding",
                    "clean_control_role_note": "In clean_control, original/edited are stable identity labels only; both descriptions are clean and identical.",
                })
    validate(inputs, mappings, len(case_ids))
    return inputs, mappings


def validate(inputs: list[dict], mappings: list[dict], n_cases: int) -> None:
    expected = n_cases * 7 * 2 * 2
    if len(inputs) != expected or len(mappings) != expected:
        raise ValueError(f"Factorial count mismatch: expected {expected}, got {len(inputs)}")
    inp = {r["experiment_id"]: r for r in inputs}
    mp = {r["experiment_id"]: r for r in mappings}
    if len(inp) != expected or inp.keys() != mp.keys():
        raise ValueError("Duplicate IDs or input/mapping mismatch")
    case_groups = {}
    for mid, m in mp.items():
        row = inp[mid]["model_input"]
        if len(row["function"]) != 2:
            raise ValueError(f"{mid}: must have two tools")
        by_role = {role: next(t for t in row["function"] if t["name"] == name)
                   for role, name in (("original", m["original_function_name"]), ("edited", m["edited_function_name"]))}
        if (m["description_condition"] == "clean_control" and
                by_role["original"]["description"] != by_role["edited"]["description"]):
            raise ValueError(f"{mid}: clean control descriptions differ")
        if m["description_condition"] != "clean_control":
            expected_desc = by_role["original"]["description"] + " " + m["cue_text"]
            if by_role["edited"]["description"] != expected_desc:
                raise ValueError(f"{mid}: cue is not the only description change")
        if [t["name"] for t in row["function"]] != [
            m["original_function_name"] if m["order"] == "original_first" else m["edited_function_name"],
            m["edited_function_name"] if m["order"] == "original_first" else m["original_function_name"],
        ]:
            raise ValueError(f"{mid}: tool order is inconsistent with role labels")
        group = (m["source_case_id"], m["description_condition"], m["name_mapping"])
        case_groups.setdefault(group, {})[m["order"]] = (m, by_role)
    for group, pair in case_groups.items():
        if set(pair) != set(ORDERS):
            raise ValueError(f"Missing order-paired cell: {group}")
        a, b = pair["original_first"][1], pair["edited_first"][1]
        if a["original"]["name"] != b["original"]["name"] or a["edited"]["name"] != b["edited"]["name"]:
            raise ValueError(f"Name identity changed when order swapped: {group}")
        for role in ("original", "edited"):
            if a[role]["description"] != b[role]["description"] or a[role]["parameters"] != b[role]["parameters"]:
                raise ValueError(f"Description/schema identity changed when order swapped: {group}/{role}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input", type=Path, default=BASE_INPUT)
    ap.add_argument("--mapping", type=Path, default=BASE_MAPPING)
    ap.add_argument("--cues", type=Path, default=CUES)
    ap.add_argument("--output-dir", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--limit-cases", type=int, help="Generate a small CPU/GPU smoke matrix for the first N source cases")
    ap.add_argument("--smoke-cases", type=int, choices=(12, 16), help="Generate a 12/16-request smoke sample over distinct cases and varied factors")
    args = ap.parse_args()
    if args.limit_cases and args.smoke_cases:
        ap.error("Choose --limit-cases or --smoke-cases, not both")
    inputs, maps = generate(read_jsonl(args.input), read_jsonl(args.mapping), json.loads(args.cues.read_text(encoding="utf-8"))["cues"], args.limit_cases)
    if args.smoke_cases:
        # Choose one request per distinct case, covering the first 3/4 description
        # levels crossed with both orders and both suffix assignments.
        factor_rows = {}
        for x, m in zip(inputs, maps):
            factor_rows[(m["description_condition"], m["order"], m["name_mapping"])] = (x, m)
        levels = ["clean_control", *[c["cue_id"] for c in json.loads(args.cues.read_text(encoding="utf-8"))["cues"]]]
        nlevels = args.smoke_cases // 4
        sample = []
        case_order = list(dict.fromkeys(m["source_case_id"] for m in maps))
        known_long = ("live_simple_188-113-0", "live_simple_67-31-0", "live_simple_70-34-0")
        if args.smoke_cases == 16:
            common = [c for c in case_order if c not in known_long][:13]
            included = [c for c in known_long if c in case_order]
            case_order = common + included + [c for c in case_order if c not in common and c not in included]
        for index in range(args.smoke_cases):
            level = levels[index % nlevels]
            order = ORDERS[(index // nlevels) % 2]
            name_map = NAME_MAPS[(index // (nlevels * 2)) % 2]
            candidate = factor_rows[(level, order, name_map)]
            # Rebind the sampled factor cell to a distinct canonical case.
            source_case = case_order[index]
            match = next((x, m) for x, m in zip(inputs, maps)
                         if m["source_case_id"] == source_case and
                         m["description_condition"] == level and m["order"] == order and m["name_mapping"] == name_map)
            sample.append(match)
        inputs = [x for x, _ in sample]
        maps = [m for _, m in sample]
        validate_smoke(inputs, maps)
    args.output_dir.mkdir(parents=True, exist_ok=False)
    write_jsonl(args.output_dir / "controlled_inputs.jsonl", inputs)
    write_jsonl(args.output_dir / "controlled_mapping.jsonl", maps)
    cell_counts = {}
    for m in maps:
        key = (m["description_condition"], m["order"], m["name_mapping"])
        cell_counts[key] = cell_counts.get(key, 0) + 1
    summary = {"cases": len({m["source_case_id"] for m in maps}), "requests": len(inputs),
               "description_conditions": len({m["description_condition"] for m in maps}),
               "orders": len({m["order"] for m in maps}),
               "name_mappings": len({m["name_mapping"] for m in maps}),
               "factorial_cells": len(cell_counts),
               "requests_per_cell_min": min(cell_counts.values()),
               "requests_per_cell_max": max(cell_counts.values()),
               "smoke_sample": bool(args.smoke_cases)}
    (args.output_dir / "design.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


def validate_smoke(inputs: list[dict], mappings: list[dict]) -> None:
    if len(inputs) not in (12, 16) or len({m["source_case_id"] for m in mappings}) != len(mappings):
        raise ValueError("Smoke sample must have 12/16 requests from distinct cases")
    expected_cells = {(m["description_condition"], m["order"], m["name_mapping"]) for m in mappings}
    if len(expected_cells) != len(mappings):
        raise ValueError("Smoke sample must cover distinct condition/order/name cells")


if __name__ == "__main__":
    main()
