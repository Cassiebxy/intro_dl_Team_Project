"""Dependency-free data contracts, output auditing, and an offline HTML report."""
from __future__ import annotations

import csv
import difflib
import hashlib
import html
import json
import re
from pathlib import Path

from . import SCHEMA_VERSION


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def text_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def read_jsonl(path: Path) -> list[dict]:
    rows = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"{path}:{number}: invalid JSON") from exc
        if not isinstance(row, dict):
            raise ValueError(f"{path}:{number}: expected an object")
        rows.append(row)
    if not rows:
        raise ValueError(f"{path}: empty dataset")
    return rows


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, ensure_ascii=False, allow_nan=False) + "\n" for row in rows), encoding="utf-8")


def unique_index(rows: list[dict], field: str) -> dict[str, dict]:
    result = {}
    for row in rows:
        value = row.get(field)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"Missing/non-string {field}")
        if value in result:
            raise ValueError(f"Duplicate {field}: {value}")
        result[value] = row
    return result


def load_inputs(path: Path) -> list[dict]:
    rows = read_jsonl(path)
    unique_index(rows, "description_id")
    for row in rows:
        if set(row) != {"description_id", "input_description"}:
            raise ValueError("Inference inputs must contain only description_id and input_description; keep gold/metadata separate")
        if not isinstance(row["input_description"], str) or not row["input_description"].strip():
            raise ValueError(f"{row['description_id']}: empty/non-string input_description")
    return rows


def load_pairs(path: Path, split: str | None = None) -> list[dict]:
    rows = read_jsonl(path)
    unique_index(rows, "example_id")
    unique_index(rows, "description_id")
    for row in rows:
        for name in ("input_description", "target_description", "source_group_id", "split"):
            if not isinstance(row.get(name), str) or not row[name].strip():
                raise ValueError(f"{row['example_id']}: missing/non-string {name}")
        if split is not None and row["split"] != split:
            raise ValueError(f"{row['example_id']}: expected split {split}, got {row['split']}")
        spans = row.get("protected_spans", [])
        if not isinstance(spans, list) or any(not isinstance(s, str) or not s for s in spans):
            raise ValueError("protected_spans must be a list of nonempty strings")
        if any(span.casefold() not in row["target_description"].casefold() for span in spans):
            raise ValueError(f"{row['example_id']}: protected span not in target")
    return rows


def validate_splits(train: list[dict], dev: list[dict]) -> dict:
    overlap = sorted({r["source_group_id"] for r in train} & {r["source_group_id"] for r in dev})
    if overlap:
        raise ValueError(f"Source groups overlap across train/dev: {overlap}")
    shared_ids = sorted({r["description_id"] for r in train} & {r["description_id"] for r in dev})
    if shared_ids:
        raise ValueError(f"Description IDs overlap across train/dev: {shared_ids}")
    shared_targets = {r["target_description"].strip().casefold() for r in train} & {
        r["target_description"].strip().casefold() for r in dev}
    if shared_targets:
        raise ValueError("Exact canonical targets overlap across train/dev; review grouping")
    return {"train_examples": len(train), "dev_examples": len(dev),
            "train_groups": len({r["source_group_id"] for r in train}),
            "dev_groups": len({r["source_group_id"] for r in dev}), "group_overlap": overlap}


def inference_rows(pairs: list[dict]) -> list[dict]:
    return [{"description_id": r["description_id"], "input_description": r["input_description"]} for r in pairs]


def audit(inputs: list[dict], outputs: list[dict], pairs: list[dict] | None = None) -> tuple[dict, list[dict]]:
    expected = unique_index(inputs, "description_id")
    observed = unique_index(outputs, "description_id")
    targets = unique_index(pairs, "description_id") if pairs else {}
    if pairs is not None and targets.keys() != expected.keys():
        raise ValueError("Gold file must cover exactly the inference input IDs")
    missing = sorted(expected.keys() - observed.keys())
    extra = sorted(observed.keys() - expected.keys())
    details = []
    contract_errors = []
    required = {"schema_version", "run_id", "description_id", "input_sha256", "normalized_description",
                "status", "error", "input_tokens", "output_tokens", "truncated"}
    for rid, source in expected.items():
        output = observed.get(rid)
        errors = []
        if output is None:
            output = {"status": "missing", "normalized_description": "", "truncated": False, "error": "missing ID"}
        else:
            if required - set(output):
                errors.append("missing required output fields")
            if output.get("input_sha256") != text_hash(source["input_description"]):
                errors.append("input hash mismatch")
            if output.get("status") not in {"ok", "error"}:
                errors.append("invalid status")
            if not isinstance(output.get("truncated"), bool):
                errors.append("truncated must be boolean")
            for key in ("input_tokens", "output_tokens"):
                value = output.get(key)
                if value is not None and (type(value) is not int or value < 0):
                    errors.append(f"invalid {key}")
            if output.get("status") == "error" and not output.get("error"):
                errors.append("error status requires an error reason")
        generated = output.get("normalized_description", "")
        if not isinstance(generated, str):
            errors.append("normalized_description must be string")
            generated = ""
        if output.get("status") == "ok" and (not generated.strip() or output.get("truncated")):
            errors.append("ok output is empty or truncated")
        if errors:
            contract_errors.append({"description_id": rid, "errors": errors})
        target = targets.get(rid)
        successful = output.get("status") == "ok" and not errors and not output.get("truncated")
        spans = target.get("protected_spans", []) if target else []
        absent = [span for span in spans if span.casefold() not in generated.casefold()]
        details.append({"description_id": rid, "input_description": source["input_description"],
                        "normalized_description": generated, "status": output.get("status"),
                        "error": output.get("error"), "truncated": output.get("truncated"),
                        "contract_errors": errors,
                        "target_description": target["target_description"] if target else None,
                        "variant": target.get("variant") if target else None,
                        "exact_match": successful and generated == target["target_description"] if target else None,
                        "protected_spans": spans, "missing_protected_spans": absent,
                        "protected_span_check": successful and not absent if spans else None})
    n = len(expected)
    scored = [r for r in details if r["exact_match"] is not None]
    checked = [r for r in details if r["protected_span_check"] is not None]
    clean = [r for r in scored if r["variant"] in {"clean_identity", "clean"}]
    metrics = {"schema_version": SCHEMA_VERSION, "n_expected": n, "n_observed": len(outputs),
               "missing_ids": missing, "extra_ids": extra, "contract_errors": contract_errors,
               "contract_valid": not (missing or extra or contract_errors),
               "ok_n": sum(r["status"] == "ok" and not r["contract_errors"] and not r["truncated"] for r in details),
               "error_or_missing_n": sum(r["status"] != "ok" or bool(r["contract_errors"]) or bool(r["truncated"]) for r in details),
               "truncated_n": sum(bool(r["truncated"]) for r in details),
               "exact_match_n": sum(r["exact_match"] for r in scored) if scored else None,
               "exact_match_rate": sum(r["exact_match"] for r in scored) / len(scored) if scored else None,
               "protected_span_pass_n": sum(r["protected_span_check"] for r in checked) if checked else None,
               "protected_span_pass_rate": sum(r["protected_span_check"] for r in checked) / len(checked) if checked else None,
               "clean_identity_exact_match_rate": sum(r["exact_match"] for r in clean) / len(clean) if clean else None,
               "interpretation": "Text recovery and literal protected-span checks. Review functional meaning separately."}
    return metrics, details


def diff_html(before: str, after: str) -> tuple[str, str]:
    left, right = [], []
    a, b = re.findall(r"\s+|\S+", before), re.findall(r"\s+|\S+", after)
    for tag, i, j, k, l in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        x, y = html.escape("".join(a[i:j])), html.escape("".join(b[k:l]))
        left.append(f"<del>{x}</del>" if tag in {"delete", "replace"} else x)
        right.append(f"<ins>{y}</ins>" if tag in {"insert", "replace"} else y)
    return "".join(left), "".join(right)


def save_report(
    directory: Path,
    metrics: dict,
    details: list[dict],
    title: str = "BART local synthetic audit",
    scope: str = "Synthetic smoke test. Review functionality preservation alongside literal constraint checks.",
) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    write_json(directory / "audit.json", metrics)
    write_jsonl(directory / "case_audit.jsonl", details)
    columns = ["description_id", "status", "variant", "exact_match", "protected_span_check", "truncated", "error"]
    with (directory / "case_summary.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        writer.writerows({k: r[k] for k in columns} for r in details)
    cases = []
    for row in details:
        before, after = diff_html(row["input_description"], row["normalized_description"])
        target = html.escape(row["target_description"] or "No target text provided")
        verdict = "Exact match" if row["exact_match"] else ("Manual review needed" if row["status"] == "ok" else "Generation failed")
        notes = html.escape(json.dumps({"status": row["status"], "missing_protected_spans": row["missing_protected_spans"],
                                       "truncated": row["truncated"], "error": row["error"]}, ensure_ascii=False))
        cases.append(f"<section><h2>{html.escape(row['description_id'])}</h2><p>{verdict}</p>"
                     f"<div class='pair'><div><h3>Input (deletions in red)</h3><p class='text'>{before}</p></div>"
                     f"<div><h3>Output (additions in green)</h3><p class='text'>{after}</p></div></div>"
                     f"<h3>Reference target</h3><p class='text'>{target}</p><p class='note'>{notes}</p></section>")
    score = metrics["exact_match_rate"]
    headline = (
        f"{metrics['exact_match_n']}/{metrics['n_expected']} exact matches ({score:.1%})"
        if score is not None else "Interface checks only. No gold target was provided."
    )
    document = """<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>__TITLE__</title><style>
body{font:16px/1.7 -apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;color:#202b35;background:#f6f8fa;margin:0}
main{max-width:1120px;margin:40px auto;padding:0 24px}h1{font-size:30px}h2{font-size:18px;overflow-wrap:anywhere}h3{font-size:14px;color:#516273}
section{padding:24px 0;border-top:1px solid #ccd5dd}.pair{display:grid;grid-template-columns:1fr 1fr;gap:32px}.text{white-space:pre-wrap;overflow-wrap:anywhere}
del{background:#ffe0e0;color:#8a1523}ins{background:#d8f3dc;color:#165a2c;text-decoration:none}.note{color:#586776;font-size:13px;overflow-wrap:anywhere}
@media(max-width:720px){.pair{grid-template-columns:1fr;gap:4px}}
</style><main><h1>__TITLE__</h1><p>__HEADLINE__</p>
<p>__SCOPE__</p>
<p>Red marks deletions in the input. Green marks additions in the output. Failed, truncated, and unmatched cases are included.</p>__CASES__</main></html>"""
    document = document.replace("__TITLE__", html.escape(title)).replace("__HEADLINE__", html.escape(headline))
    document = document.replace("__SCOPE__", html.escape(scope)).replace("__CASES__", "".join(cases))
    (directory / "rewrite_report.html").write_text(document, encoding="utf-8")
