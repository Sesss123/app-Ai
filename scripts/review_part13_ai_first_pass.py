"""Add an AI first-pass recommendation without claiming human approval."""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "reports" / "part11" / "evaluation" / "human_review_queue.jsonl"
OUTPUT = ROOT / "reports" / "part13" / "ai_reviewed_queue.jsonl"
SUMMARY = ROOT / "reports" / "part13" / "ai_review_summary.json"

APPROVE_FLAGGED = {
    "gold-422", "gold-165", "gold-279", "gold-211", "gold-274",
    "gold-389", "gold-304", "gold-331", "gold-283",
}


def main():
    rows = [json.loads(line) for line in SOURCE.read_text(encoding="utf-8").splitlines() if line]
    counts = {"Approve": 0, "Edit": 0, "Reject": 0}
    reviewed = []
    for row in rows:
        if row["review_priority"] == "sampled_pass":
            recommendation = "Approve"
            rationale = "Passed all automatic checks and was selected as a quality-control sample."
            suggestion = ""
        elif row["eval_id"] in APPROVE_FLAGGED:
            recommendation = "Approve"
            rationale = "The answer addresses accessibility; this appears to be a scenario-keyword checker false positive."
            suggestion = ""
        else:
            recommendation = "Edit"
            suggestion = row["reference_answer"]
            reasons = set(row.get("review_reasons", []))
            if "place_name_coverage" in reasons:
                rationale = "The generated answer omits or misspells one or more required place names."
            elif "repetition" in reasons:
                rationale = "The response repeats a template and does not provide the requested comparison."
            else:
                rationale = "The response is off-scenario, unclear, or contains unsupported/awkward wording."
        counts[recommendation] += 1
        reviewed.append({
            **row,
            "ai_recommendation": recommendation,
            "ai_rationale": rationale,
            "ai_suggested_answer": suggestion,
            "ai_reviewer": "Codex AI first pass (not human approval)",
        })
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in reviewed) + "\n", encoding="utf-8")
    result = {
        "status": "ai_first_pass_complete_human_confirmation_required",
        "rows": len(reviewed),
        "recommendation_counts": counts,
        "human_approval_granted": False,
    }
    SUMMARY.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
