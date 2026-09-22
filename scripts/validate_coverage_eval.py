"""Validate the 10,000-item automated coverage evaluation artifact."""

import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SPEC = json.loads((ROOT / "config" / "coverage_eval_spec.json").read_text(encoding="utf-8"))
PATH = ROOT / "data" / "evaluation" / "coverage_v0.1.0" / "coverage_eval_10000.jsonl"


def main() -> None:
    rows = [json.loads(line) for line in PATH.read_text(encoding="utf-8").splitlines() if line.strip()]
    errors = []
    if len(rows) != SPEC["total_prompts"]:
        errors.append(f"row count {len(rows)}")
    if len({row["eval_id"] for row in rows}) != len(rows):
        errors.append("duplicate eval IDs")
    if Counter(row["language"] for row in rows) != Counter(SPEC["languages"]):
        errors.append("language distribution mismatch")
    if Counter(row["scenario"] for row in rows) != Counter(SPEC["scenarios"]):
        errors.append("scenario distribution mismatch")
    if any(not row["prompt"].strip() or not row["context_place_ids"] for row in rows):
        errors.append("blank prompt or context")
    if any(not all(row["source_urls"]) for row in rows):
        errors.append("missing source URL")
    if errors:
        raise SystemExit("Coverage validation failed: " + "; ".join(errors))
    print(f"Coverage validation passed: {len(rows)} rows")


if __name__ == "__main__":
    main()

