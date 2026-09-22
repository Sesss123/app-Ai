"""Create an evidence-based AI audit of the Part 8 automatic review queue.

This is not a substitute for the mandatory human release approval.
"""

import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
QUEUE = ROOT / "reports" / "part08" / "corrective_eval" / "human_review_queue.jsonl"
OUTPUT = ROOT / "reports" / "part08" / "corrective_eval" / "ai_flag_audit.json"

# Manual inspection of the 18 automatically flagged outputs. These labels only
# prioritize human review; they never grant release approval.
MODEL_ERRORS = {
    "gold-061": "misses one compared place and contains a broken placeholder/mixed-script fragment",
    "gold-350": "does not name the requested place and confuses 'honda' with Honda",
    "gold-196": "generic itinerary response omits all requested place names",
    "gold-274": "vague verification response does not address family accessibility",
    "gold-389": "answers about price instead of family accessibility",
    "gold-470": "does not answer the culture/etiquette request",
    "gold-397": "omits two itinerary places and switches to an etiquette template",
    "gold-355": "contains the replacement character and mixes price/accessibility advice",
    "gold-264": "generic itinerary response omits all requested place names",
    "gold-283": "answers about price instead of family accessibility",
    "gold-120": "generic itinerary response omits all requested place names",
    "gold-254": "does not answer the culture/etiquette request",
    "gold-388": "generic itinerary response omits all requested place names",
}

LIKELY_CHECKER_FALSE_POSITIVES = {
    "gold-141": "parallel wording is expected in a two-place comparison",
    "gold-211": "Sinhala answer discusses entrances, toilets, paths and parking",
    "gold-224": "English answer explicitly asks the venue to confirm accessibility",
    "gold-002": "uncertainty answer correctly recommends checking a current official source",
    "gold-106": "Singlish answer discusses entrance, path, toilet and parking accessibility",
}


def main():
    if not QUEUE.is_file():
        raise FileNotFoundError("Import the Part 8 output before running this audit")

    rows = [json.loads(line) for line in QUEUE.read_text(encoding="utf-8").splitlines() if line]
    row_ids = {row["eval_id"] for row in rows}
    classified_ids = set(MODEL_ERRORS) | set(LIKELY_CHECKER_FALSE_POSITIVES)
    if row_ids != classified_ids:
        missing = sorted(row_ids - classified_ids)
        stale = sorted(classified_ids - row_ids)
        raise ValueError(f"Audit mapping mismatch; missing={missing}, stale={stale}")

    findings = []
    for row in rows:
        eval_id = row["eval_id"]
        if eval_id in MODEL_ERRORS:
            classification = "probable_model_error"
            reason = MODEL_ERRORS[eval_id]
        else:
            classification = "likely_checker_false_positive"
            reason = LIKELY_CHECKER_FALSE_POSITIVES[eval_id]
        findings.append({
            "eval_id": eval_id,
            "language": row["language"],
            "scenario": row["scenario"],
            "classification": classification,
            "reason": reason,
            "automatic_checks": row["automatic_checks"],
        })

    report = {
        "status": "ai_audit_requires_human_review",
        "release_decision": "blocked",
        "automatic_flagged_rows": len(rows),
        "probable_model_errors": len(MODEL_ERRORS),
        "likely_checker_false_positives": len(LIKELY_CHECKER_FALSE_POSITIVES),
        "model_error_scenarios": dict(Counter(
            row["scenario"] for row in rows if row["eval_id"] in MODEL_ERRORS
        )),
        "recommended_actions": [
            "Add corrective examples for itinerary place retention, family accessibility, and culture etiquette.",
            "Add corruption checks for replacement characters, foreign-script fragments, and leaked placeholders.",
            "Expand Sinhala and Singlish scenario keyword rules before using automatic relevance as a gate.",
            "Re-run Part 7 corrective training and Part 8 evaluation, then obtain independent human approval.",
        ],
        "findings": findings,
    }
    OUTPUT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({key: value for key, value in report.items() if key != "findings"}, indent=2))


if __name__ == "__main__":
    main()
