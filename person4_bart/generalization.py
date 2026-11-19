"""Build versioned held-out BFCL text inputs with a separate scoring file."""
from __future__ import annotations

import argparse
import difflib
import json
import re
from collections import Counter
from pathlib import Path

from .core import inference_rows, load_pairs, read_jsonl, sha256, text_hash, unique_index, write_json, write_jsonl

HERE = Path(__file__).resolve().parent
PROTOCOL = HERE / "protocols" / "shared_bfcl_v1.json"
PACKAGE = HERE / "data" / "generalization_v1"


def shared_data(protocol_path: Path = PROTOCOL):
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    root = HERE.parent / protocol["shared_data"]
    manifest = root / "manifest.json"
    if sha256(manifest) != protocol["shared_data_manifest_sha256"]:
        raise ValueError("Unexpected Person 2 manifest SHA-256")
    hashes = json.loads(manifest.read_text(encoding="utf-8"))["hashes"]
    for filename, digest in hashes.items():
        if sha256(root / filename) != digest:
            raise ValueError(f"Unexpected hash for {filename}")
    return protocol, root


def observed_cues(pairs):
    cues = set()
    for row in pairs:
        original, edited = row["target_description"], row["input_description"]
        if edited == original:
            continue
        if edited.startswith(original + " "):
            cues.add(edited[len(original):].strip())
        elif edited.endswith(" " + original):
            cues.add(edited[:-len(original)].strip())
        else:
            raise ValueError(f"Unexpected cue construction in {row['example_id']}")
    return sorted(cues)


def normalized(text):
    return " ".join(re.findall(r"\w+", text.casefold()))


def build(protocol_path: Path, output: Path):
    protocol, data = shared_data(protocol_path)
    splits = {s: load_pairs(data / f"pairs_{s}.jsonl", s) for s in ("train", "dev", "test")}
    for key in ("source_group_id", "source_tool_id", "description_id", "target_description"):
        values = [{r[key] for r in rows} for rows in splits.values()]
        if any(a & b for i, a in enumerate(values) for b in values[i + 1:]):
            raise ValueError(f"{key} crosses the shared train/dev/test partitions")
    cases_by_split = {s: {case for row in rows for case in row["source_case_ids"]} for s, rows in splits.items()}
    if sum(map(len, cases_by_split.values())) != len(set.union(*cases_by_split.values())):
        raise ValueError("Source case ID crosses shared partitions")
    train_cues, dev_cues = (observed_cues(splits[s]) for s in ("train", "dev"))
    prior_templates = {normalized(s) for s in train_cues + dev_cues}
    controlled_cues = unique_index(json.loads((HERE.parent / "table3" / "table3_cues.json").read_text())["cues"], "cue_id")
    cues = protocol["generalization_cues"]
    unique_index(cues, "cue_id")
    if len({normalized(r["text"]) for r in cues}) != len(cues):
        raise ValueError("Duplicate test template")
    reviewed = []
    for entry in cues:
        cue = entry["text"]
        common = normalized(cue) in prior_templates
        if entry["slice"] == "seen_cue":
            if cue not in train_cues or controlled_cues[entry["cue_id"]]["text"] != cue:
                raise ValueError("Seen cue does not match Person 2 training and the controlled baseline")
        elif common:
            raise ValueError(f"Proposed held-out wording appears in train or dev: {entry['cue_id']}")
        nearest = max(train_cues + dev_cues, key=lambda s: difflib.SequenceMatcher(None, normalized(s), normalized(cue)).ratio())
        reviewed.append({**entry, "placement": "suffix", "observed_in_train_or_dev": common,
                         "nearest_train_dev_wording": nearest,
                         "normalized_character_similarity": round(difflib.SequenceMatcher(None, normalized(nearest), normalized(cue)).ratio(), 4),
                         "review": "Single nonfunctional sentence. Canonical capabilities and conditions remain verbatim.",
                         "provenance": "Controlled Table 3 cue 1" if common else "Person 4 synthetic cue, predeclared in the protocol"})
    clean = [r for r in splits["test"] if r["variant"] == "clean"]
    unique_index(clean, "source_tool_id")
    seen_ids = {r["description_id"] for s in ("train", "dev") for r in splits[s]}
    rows = []
    for source in clean:
        target = source["target_description"]
        for cue in [None, *reviewed]:
            text = target if cue is None else target + " " + cue["text"]
            rid = "desc_" + text_hash(text)
            if rid in seen_ids:
                raise ValueError(f"Test description ID seen in development: {rid}")
            cue_id = cue["cue_id"] if cue else None
            rows.append({**source, "example_id": f"p4_test_{text_hash(source['source_tool_id'] + ':' + str(cue_id))}",
                         "description_id": rid, "input_description": text, "variant": cue_id or "clean",
                         "cue_id": cue_id, "cue_family": cue["family"] if cue else None,
                         "slice": cue["slice"] if cue else "clean", "source_tool_seen": False,
                         "provenance": "Canonical Person 2 test description with versioned Person 4 cue"})
    unique_index(rows, "description_id")
    output.mkdir(parents=True, exist_ok=False)
    write_jsonl(output / "pairs_test.jsonl", rows)
    write_jsonl(output / "normalizer_inputs_test.jsonl", inference_rows(rows))
    write_jsonl(output / "cues.jsonl", reviewed)
    case_rows = [{"source_case_id": c, "source_tool_id": row["source_tool_id"],
                  "source_group_id": row["source_group_id"],
                  "query_overlaps_train": c == protocol["duplicate_query"]["test_case_id"]}
                 for row in clean for c in row["source_case_ids"]]
    unique_index(case_rows, "source_case_id")
    write_jsonl(output / "cases_test.jsonl", case_rows)
    manifest = {"protocol_id": protocol["protocol_id"], "protocol_sha256": sha256(protocol_path),
                "shared_data_manifest_sha256": protocol["shared_data_manifest_sha256"],
                "test_cases": len(case_rows), "test_source_tools": len(clean),
                "test_source_groups": len({r["source_group_id"] for r in case_rows}),
                "pairs_by_slice": dict(Counter(r["slice"] for r in rows)),
                "train_cues": train_cues, "dev_cues": dev_cues,
                "duplicate_query": protocol["duplicate_query"],
                "files": {p.name: sha256(p) for p in sorted(output.glob("*.jsonl"))}}
    write_json(output / "manifest.json", manifest)
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol", type=Path, default=PROTOCOL)
    parser.add_argument("--output", type=Path, default=PACKAGE)
    args = parser.parse_args()
    manifest = build(args.protocol, args.output)
    print(json.dumps({k: manifest[k] for k in ("test_cases", "test_source_tools", "test_source_groups", "pairs_by_slice")}, indent=2))
