"""Validate the Part 3 scaffold or the final human-reviewed gold set."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SPEC_PATH = ROOT / "config" / "gold_eval_spec.json"
DEFAULT_PATH = ROOT / "data" / "evaluation" / "gold_v0.1.0" / "gold_scaffold.jsonl"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", type=Path, default=DEFAULT_PATH)
    parser.add_argument("--mode", choices=("scaffold", "draft", "final"), default="scaffold")
    args = parser.parse_args()
    spec = json.loads(SPEC_PATH.read_text(encoding="utf-8"))
    rows = [json.loads(line) for line in args.path.read_text(encoding="utf-8").splitlines() if line.strip()]
    errors = []
    ids = [row.get("eval_id") for row in rows]
    if args.mode != "draft" and len(rows) != spec["total_prompts"]:
        errors.append(f"expected {spec['total_prompts']} rows, found {len(rows)}")
    if len(set(ids)) != len(ids):
        errors.append("duplicate eval_id values")
    if args.mode == "draft":
        if any(row.get("language") not in spec["languages"] for row in rows):
            errors.append("unknown language in draft")
        if any(row.get("scenario") not in spec["scenarios"] for row in rows):
            errors.append("unknown scenario in draft")
    else:
        if Counter(row.get("language") for row in rows) != Counter(spec["languages"]):
            errors.append("language distribution mismatch")
        if Counter(row.get("scenario") for row in rows) != Counter(spec["scenarios"]):
            errors.append("scenario distribution mismatch")
    if any(not row.get("target_place_ids") for row in rows):
        errors.append("one or more rows have no target places")
    if args.mode in {"draft", "final"}:
        for row in rows:
            if not str(row.get("prompt", "")).strip():
                errors.append(f"{row.get('eval_id')}: missing prompt")
            if not str(row.get("reference_answer", "")).strip():
                errors.append(f"{row.get('eval_id')}: missing reference answer")
    if args.mode == "final":
        for row in rows:
            if row.get("review_status") != spec["final_review_status"]:
                errors.append(f"{row.get('eval_id')}: not approved")
            if not row.get("author_id") or not row.get("reviewer_id"):
                errors.append(f"{row.get('eval_id')}: missing author/reviewer")
    if errors:
        print("Gold evaluation validation FAILED")
        for error in errors[:30]:
            print(f"- {error}")
        raise SystemExit(1)
    print(f"Gold evaluation {args.mode} validation passed: {len(rows)} rows")


if __name__ == "__main__":
    main()
