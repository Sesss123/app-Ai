"""Run scenario-aware checks on Part 7B targeted generations."""

import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "artifacts" / "part07_corrective" / "targeted_validation_generations.jsonl"
OUTPUT = ROOT / "reports" / "part07" / "targeted_generation_review.json"

MARKERS = {
    "current_fact_refusal": ("විවෘත", "ගාස්තුව", "තහවුරු"),
    "budget_uncertainty": ("මිල", "ගාස්තුව", "වියදම්"),
    "family_accessibility": ("ප්‍රවේශ", "පහසුකම්", "රෝද පුටුව"),
    "culture_etiquette": ("උපදෙස්", "නීති", "හැසිර"),
}


def main():
    rows = [json.loads(line) for line in SOURCE.read_text(encoding="utf-8").splitlines() if line.strip()]
    results = []
    for index, row in enumerate(rows, 1):
        answer = row["generated"]
        scenario = row["scenario"]
        markers = MARKERS[scenario]
        marker_hits = sum(marker in answer for marker in markers)
        wrong_accessibility_for_budget = scenario == "budget_uncertainty" and ("රෝද පුටුව" in answer or "පවුලකට" in answer)
        passed = marker_hits >= 1 and not wrong_accessibility_for_budget and not row.get("hit_token_limit", False)
        results.append({
            "sample": index,
            "scenario": scenario,
            "passed": passed,
            "marker_hits": marker_hits,
            "wrong_accessibility_for_budget": wrong_accessibility_for_budget,
            "prompt": row["prompt_messages"][-1]["content"],
            "generated": answer,
        })
    failed = [row for row in results if not row["passed"]]
    report = {
        "status": "targeted_review_complete_part08_required",
        "rows": len(results),
        "passed": len(results) - len(failed),
        "failed": len(failed),
        "pass_rate": (len(results) - len(failed)) / len(results),
        "scenario_counts": dict(Counter(row["scenario"] for row in results)),
        "failed_rows": failed,
        "release_status": "not_for_production_part08_evaluation_required",
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
