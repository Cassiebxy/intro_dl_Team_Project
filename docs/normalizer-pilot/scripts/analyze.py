"""Summarize paired development cases and render dependency-free SVG charts."""
import argparse
import csv
import html
import json
from collections import Counter
from pathlib import Path


def read_jsonl(path):
    return [json.loads(line) for line in path.read_text().splitlines()]


def save_csv(path, rows):
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def plot(path, title, note, labels, panels):
    width = 920
    height = 135 + 44 * len(labels) * len(panels) + 48 * len(panels)
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img">',
             f'<title>{html.escape(title)}</title>',
             '<rect width="100%" height="100%" fill="#fff"/>',
             '<g font-family="system-ui,sans-serif" fill="#182639">']

    def label(x, y, value, size=15):
        parts.append(f'<text x="{x}" y="{y}" font-size="{size}">{html.escape(str(value))}</text>')

    label(28, 38, title, 25)
    label(28, 65, note, 14)
    y = 105
    for heading, values in panels:
        label(28, y, heading, 18)
        y += 30
        for name, (count, n) in zip(labels, values):
            label(28, y + 5, name)
            parts.append(f'<rect x="320" y="{y-13}" width="450" height="22" rx="3" fill="#e8edf3"/>')
            parts.append(f'<rect x="320" y="{y-13}" width="{450*count/n:.2f}" height="22" rx="3" fill="#21678d"/>')
            label(785, y + 5, f"{count}/{n} ({count/n:.0%})")
            y += 44
        y += 18
    path.write_text("\n".join(parts + ["</g></svg>"]))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pilot", type=Path, help="Path to the original pilot directory")
    parser.add_argument("output", type=Path, help="Folder for public summaries")
    args = parser.parse_args()
    qwen = args.pilot / "qwen-four-conditions"
    results = args.output / "results"
    figures = args.output / "figures"
    for folder in (results, figures):
        folder.mkdir(parents=True, exist_ok=True)

    requests = {r["id"]: r for r in read_jsonl(qwen / "requests.jsonl")}
    scores = {r["id"]: r for r in read_jsonl(qwen / "full/scores.jsonl")}
    assert requests.keys() == scores.keys() and len(scores) == 176
    cells = {}
    public_rows = []
    for key, request in requests.items():
        score = scores[key]
        calls, diagnoses = score["calls"], score["diagnostics"]
        row = dict(case_id=request["case_id"], source_group=request["source_group"],
                   order=request["order"], condition=request["condition"],
                   rec=int(len(calls) == len(diagnoses) == 1 and diagnoses[0]["valid"]),
                   edited_selected=int(any(request["roles"]["edited"] in c for c in calls)),
                   parse_failed=int(score["status"] == "parse_error"))
        cells[(row["order"], row["condition"], row["case_id"])] = row
        public_rows.append(row)
    save_csv(results / "case_outcomes.csv", public_rows)

    conditions = ["clean", "manipulated", "normalized", "clean_normalized"]
    names = ["Clean", "Manipulated", "Manipulated → normalizer", "Clean → normalizer"]
    cases = sorted({r["case_id"] for r in public_rows})
    comparisons = []
    panels = {"rec": [], "edited_selected": []}
    for order in ["original_first", "edited_first"]:
        for metric in panels:
            panels[metric].append((order.replace("_", " ").title(), [
                (sum(cells[order, condition, case][metric] for case in cases), len(cases))
                for condition in conditions
            ]))
        for before, after in [("clean", "manipulated"), ("manipulated", "normalized"),
                              ("clean", "clean_normalized"), ("clean", "normalized")]:
            for metric in panels:
                changes = Counter(cells[order, after, case][metric] -
                                  cells[order, before, case][metric] for case in cases)
                comparisons.append(dict(order=order, before=before, after=after, metric=metric,
                                        n=len(cases), zero_to_one=changes[1], one_to_zero=changes[-1],
                                        unchanged=changes[0], net_percentage_points=round(
                                            100*(changes[1]-changes[-1])/len(cases), 2)))
    save_csv(results / "paired_transitions.csv", comparisons)
    plot(figures / "strict-correctness.svg", "Strict response correctness",
         "Initial development pilot • 22 paired cases per cell • parse failures retained",
         names, panels["rec"])
    plot(figures / "edited-selection.svg", "Edited tool selection by position",
         "Initial development pilot • Edited retains the same tool name when order changes",
         names, panels["edited_selected"])

    counts = {}
    for row in read_jsonl(args.pilot / "first-train/rewrites.jsonl"):
        counts.setdefault(row["condition"], []).append(row["exact"])
    rewrite_rows = [dict(condition=key, exact=sum(values), total=len(values))
                    for key, values in counts.items()]
    save_csv(results / "rewrite_exact_match.csv", rewrite_rows)
    plot(figures / "rewrite-exact-match.svg", "Description recovery by input variant",
         "Each variant reuses the same 22 development descriptions",
         [r["condition"].replace("_", " ").title() for r in rewrite_rows],
         [("Exact match to original description", [(r["exact"], r["total"]) for r in rewrite_rows])])


if __name__ == "__main__":
    main()
