"""Verify existing Part3 evidence and prepare the local handoff; never push Git.

Run after the portable replay and independent_audit.py. Requires the unchanged
original ZIP and its extracted directory. Standard library only, no network/GPU.
The explicit artifact list excludes personal files and the extracted source tree.
"""
import csv
import datetime
import hashlib
import json
import math
import pathlib
import re
import shutil
import sys
from zoneinfo import ZoneInfo


def check(condition, message):
    if not condition:
        raise AssertionError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def rows(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def main():
    review = pathlib.Path(__file__).resolve().parents[1]
    handoff = review.parents[1]
    repo = handoff.parents[2]
    metadata = read(handoff / "PACKAGE_METADATA.json")
    bundle = handoff / metadata["extracted_root"]
    check(sha(handoff / metadata["package"]) == metadata["sha256"], "ZIP hash")
    check(sha(bundle / "MANIFEST.json") == metadata["inner_manifest_sha256"], "manifest hash")
    fixed = read(bundle / "MANIFEST.json")["files"]
    for name, expected in fixed.items():
        target = (bundle / name).resolve()
        check(target.is_relative_to(bundle) and sha(target) == expected, "frozen file: " + name)

    replay_dir = review / "evidence/replay"
    verification = read(replay_dir / "verification_result.json")
    audit = read(review / "evidence/audit_result.json")
    check(verification["per_request_scores_equal"] and verification["summaries_equal"], "portable replay")
    check(verification["manifest_sha256"] == metadata["inner_manifest_sha256"], "replay source bundle")
    check(audit["status"] == "PASS" and audit["scores_changed"] is False, "supplementary audit")
    check(audit["source_manifest_sha256"] == metadata["inner_manifest_sha256"], "audit source bundle")
    check(audit["audit_script_sha256"] == sha(review / "evidence/independent_audit.py"), "audit script receipt")
    check(verification["requests"] == audit["requests"] == 3096, "request count")
    snapshot = bundle / "evidence/run_snapshot/full"
    replay_scores = rows(replay_dir / "replayed_scores.jsonl")
    replay_summary = read(replay_dir / "replayed_summary.json")
    check(replay_scores == rows(snapshot / "scores.jsonl"), "actual replay score records")
    check(replay_summary == read(snapshot / "summary.json"), "actual replay summaries")
    # Validate the two original summary CSVs explicitly before copying them.
    pooled = {s["cue_id"]: s for s in replay_summary}
    ordered = {}
    for item in audit["order_counts"]:
        cue, order = item["cue_id"], item["order"]
        group = [s for s in replay_scores if s["cue_id"] == cue and s["order"] == order]
        ordered[cue, order] = {
            "cue_id": cue, "order": order, "denominator": item["N"], "completed": len(group), "missing": 0,
            "edited_cur": item["edited"] / item["N"], "original_cur": item["original"] / item["N"],
            "ratio": item["ratio"], "cr": item["cr"] / item["N"],
            "technical_failures": sum(s["status"] == "technical_error" for s in group),
            "parse_failures": sum(s["status"] == "parse_error" for s in group),
        }
    for filename, reference in (("baseline_table3_results.csv", pooled), ("results_by_order.csv", ordered)):
        with (snapshot / filename).open(encoding="utf-8", newline="") as handle:
            data = list(csv.DictReader(handle))
        keys = [(int(r["cue_id"]), r["order"]) if "order" in r else int(r["cue_id"]) for r in data]
        check(len(keys) == len(set(keys)) == len(reference) and set(keys) == set(reference), "summary CSV groups")
        for actual, key in zip(data, keys):
            for field, expected in reference[key].items():
                if expected is None:
                    check(actual[field] == "", "undefined summary ratio")
                elif isinstance(expected, str):
                    check(actual[field] == expected, "summary text field")
                else:
                    check(math.isclose(float(actual[field]), expected, rel_tol=1e-12, abs_tol=1e-12), "summary numeric field: " + field)
    upstream_receipt = read(review / "evidence/UPSTREAM_SOURCE_CHECK.json")
    check(upstream_receipt["all_match"] and len(upstream_receipt["checks"]) == 9, "upstream receipt")
    for record in upstream_receipt["checks"]:
        data = (bundle / "evidence/reference_upstream" / record["path"]).read_bytes()
        blob = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
        check(blob == record["local_git_blob_sha"] == record["remote_git_blob_sha"], "upstream source identity")

    results = review / "results"
    results.mkdir(exist_ok=True)
    exports = [
        ("tables/per_case_scores.csv", "per_request_scores.csv", 3096),
        ("evidence/run_snapshot/full/baseline_table3_results.csv", "summary_by_cue.csv", 6),
        ("evidence/run_snapshot/full/results_by_order.csv", "summary_by_order.csv", 12),
        ("tables/response_failure_counts.csv", "response_failure_counts.csv", 5),
        ("tables/call_diagnostic_counts.csv", "call_diagnostic_counts.csv", 11),
    ]
    export_receipts = []
    for source_name, destination_name, expected_count in exports:
        source, destination = bundle / source_name, results / destination_name
        with source.open(encoding="utf-8", newline="") as handle:
            count = len(list(csv.DictReader(handle)))
        check(count == expected_count, "export rows: " + destination_name)
        shutil.copyfile(source, destination)
        check(sha(source) == sha(destination), "byte-identical export: " + destination_name)
        export_receipts.append({"destination": "results/" + destination_name,
                                "source_inside_bundle": source_name, "rows": count, "sha256": sha(destination)})
    (results / "README.md").write_text(
        "# 已核实的原版评分结果\n\n"
        "这些文件是原交接包内已核实结果的字节一致副本，方便 Part4 直接使用；没有新增或修改分数。"
        "来源 run：`baseline-table3-qwen7b-20261020-mps`。逐文件来源和 SHA256 见上层 DELIVERY_MANIFEST.json。\n\n"
        "| 文件 | 行数 | 单位/说明 |\n|---|---:|---|\n"
        "| [per_request_scores.csv](per_request_scores.csv) | 3096 | 每请求一行，布尔分数为 0/1 |\n"
        "| [summary_by_cue.csv](summary_by_cue.csv) | 6 | 每 cue N=516；CUR/CR 为 0–1，ratio 无单位 |\n"
        "| [summary_by_order.csv](summary_by_order.csv) | 12 | 每 cue/order N=258；CUR/CR 为 0–1，空 ratio 为 undefined |\n"
        "| [response_failure_counts.csv](response_failure_counts.csv) | 5 | 请求级互斥分类，合计 3096；pct 为 0–100% |\n"
        "| [call_diagnostic_counts.csv](call_diagnostic_counts.csv) | 11 | 调用级分类，合计 3038 calls，不是请求数 |\n\n"
        "评分解释、空数组和 optional-answer 限制见 [REVIEW_REPORT](../REVIEW_REPORT.md)。"
        "两个 CUR 可重叠；CR 不是 strict-all。真人签收状态以 [STATUS](../STATUS.json)为准。\n",
        encoding="utf-8")

    now = datetime.datetime.now(ZoneInfo("America/New_York")).isoformat()
    status_path = review / "STATUS.json"
    status = read(status_path)
    check(status["technical_review_status"] == "PASS", "technical status")
    # Preserve the actual human decision. This command never signs for anyone.
    human_accepted = status.get("human_signoff") == "PASS"
    remaining = ["Commit and push the selected Part3 files"]
    if not human_accepted:
        remaining.insert(0, "Read review evidence and record an actual human signoff decision")
    status.update({"delivery_status": "COMPLETE", "delivery_manifest": "DELIVERY_MANIFEST.json",
                   "acceptance_checklist": "ACCEPTANCE_CHECKLIST.md", "part4_handoff": "HANDOFF_TO_PART4.md",
                   "human_signoff_form": "HUMAN_SIGNOFF.md", "commit_files": "COMMIT_FILES.txt",
                   "delivery_prepared_at": now,
                   "part3_status": "COMPLETE" if human_accepted else "TECHNICAL_COMPLETE_AWAITING_HUMAN_SIGNOFF",
                   "remaining_user_actions": remaining})
    status_path.write_text(json.dumps(status, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    artifacts = [
        "README.md", "REVIEW_REPORT.md", "LEFTOVERS.md", "STATUS.json",
        "ACCEPTANCE_CHECKLIST.md", "HANDOFF_TO_PART4.md", "HUMAN_SIGNOFF.md", "PUSH_INSTRUCTIONS.md",
        "evidence/independent_audit.py", "evidence/prepare_delivery.py", "evidence/audit_result.json",
        "evidence/metric_boundary_results.json", "evidence/CASE_REVIEW.md", "evidence/sampled_cases.json",
        "evidence/RUN_RECORD.json", "evidence/UPSTREAM_SOURCE_CHECK.json", "evidence/SOURCE_AND_PROMPT_REVIEW.md",
        "evidence/replay/verification_result.json", "evidence/replay/replayed_summary.json",
        "evidence/replay/replayed_scores.jsonl", "results/README.md",
    ] + ["results/" + destination for _, destination, _ in exports]
    all_paths = sorted(artifacts + ["COMMIT_FILES.txt", "DELIVERY_MANIFEST.json"])
    for name in artifacts:
        check((review / name).is_file(), "missing delivery artifact: " + name)
    (review / "COMMIT_FILES.txt").write_text(
        "".join((review / name).relative_to(repo).as_posix() + "\n" for name in all_paths), encoding="utf-8")
    # The manifest excludes itself to avoid a self-referential hash.
    manifest_paths = artifacts + ["COMMIT_FILES.txt"]
    delivery = {"prepared_at": now, "reviewer_type": "assistant", "human_signoff": status["human_signoff"],
                "human_reviewer": status.get("human_reviewer"),
                "human_signoff_recorded_at": status.get("human_signoff_recorded_at"),
                "part3_status": status["part3_status"],
                "technical_review_status": "PASS", "delivery_status": "COMPLETE", "scores_changed": False,
                "source_commit": status["source_commit"], "source_bundle_sha256": metadata["sha256"],
                "source_manifest_sha256": metadata["inner_manifest_sha256"],
                "python_version": sys.version, "all_frozen_files_unchanged": True,
                "file_paths_relative_to": "reviews/part3/", "manifest_self_excluded": True,
                "export_receipts": export_receipts,
                "files": {name: {"sha256": sha(review / name), "bytes": (review / name).stat().st_size}
                          for name in sorted(manifest_paths)}}
    (review / "DELIVERY_MANIFEST.json").write_text(json.dumps(delivery, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for name in all_paths:
        path = review / name
        if path.suffix == ".json":
            read(path)
        if path.suffix == ".md":
            for link in re.findall(r"\]\(([^)]+)\)", path.read_text(encoding="utf-8")):
                if "://" not in link:
                    check((path.parent / link.split("#")[0]).exists(), "broken link: " + name + " -> " + link)
    for name, expected in fixed.items():
        check(sha(bundle / name) == expected, "frozen file changed after export: " + name)
    print(json.dumps({"technical_review_status": "PASS", "delivery_status": "COMPLETE",
                      "human_signoff": status["human_signoff"], "scores_changed": False,
                      "commit_file_count": len(all_paths), "verified_export_rows": [r[2] for r in exports],
                      "source_files_unchanged": len(fixed), "git_mutations_performed": False}, indent=2))


if __name__ == "__main__":
    main()
