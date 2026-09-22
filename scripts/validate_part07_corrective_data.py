"""Validate Part 7 corrective and combined training splits."""

import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
BASE = ROOT / "data" / "training" / "corrective_v0.3.0"
HOLDOUT = ROOT / "data" / "evaluation" / "gold_v0.1.0" / "holdout_place_ids.txt"


def load(name):
    return [json.loads(x) for x in (BASE / name).read_text(encoding="utf-8").splitlines() if x.strip()]


def main():
    corrective_train = load("corrective_train_draft.jsonl")
    corrective_val = load("corrective_validation_draft.jsonl")
    train = load("combined_train_candidate.jsonl")
    val = load("combined_validation_candidate.jsonl")
    holdout = {x.strip() for x in HOLDOUT.read_text(encoding="utf-8").splitlines() if x.strip()}
    train_ids = {pid for row in train for pid in row["place_ids"]}
    val_ids = {pid for row in val for pid in row["place_ids"]}
    all_ids = train_ids | val_ids
    errors = []

    if (len(corrective_train), len(corrective_val), len(train), len(val)) != (900, 150, 1800, 250):
        errors.append("unexpected row counts")
    if train_ids & val_ids:
        errors.append(f"train/validation overlap: {len(train_ids & val_ids)}")
    if all_ids & holdout:
        errors.append(f"gold holdout overlap: {len(all_ids & holdout)}")

    pairs = Counter()
    for index, row in enumerate(corrective_train + corrective_val, 1):
        if [m.get("role") for m in row.get("messages", [])] != ["system", "user", "assistant"]:
            errors.append(f"row {index}: invalid roles")
            continue
        system, user, answer = [m["content"].strip() for m in row["messages"]]
        if not system or not user or not answer:
            errors.append(f"row {index}: blank message")
        if "�" in system + user + answer or "ප්‍ā" in system + user + answer:
            errors.append(f"row {index}: encoding artifact")
        name_line = next((line for line in system.splitlines() if line.startswith(("ස්ථානය: ", "Place: "))), "")
        place_name = name_line.split(": ", 1)[1] if ": " in name_line else ""
        if not place_name or place_name.casefold() not in answer.casefold():
            errors.append(f"row {index}: place name missing from answer")
        if row["scenario"] in {"current_fact_refusal", "budget_uncertainty"}:
            markers = {
                "si": ("තහවුරු කළ නොහැක", "සඳහන් නොවේ", "දත්තවල නැත"),
                "singlish": ("confirm karanna ba", "data wala naha"),
                "en": ("do not confirm", "does not include"),
            }
            if not any(marker in answer for marker in markers[row["lang"]]):
                errors.append(f"row {index}: current/budget refusal missing")
        pairs[(system, user, answer)] += 1
    duplicates = sum(count - 1 for count in pairs.values() if count > 1)
    if duplicates:
        errors.append(f"exact duplicate examples: {duplicates}")

    result = {
        "status": "passed" if not errors else "failed",
        "errors": errors[:100],
        "corrective_train_rows": len(corrective_train),
        "corrective_validation_rows": len(corrective_val),
        "combined_train_rows": len(train),
        "combined_validation_rows": len(val),
        "train_validation_place_overlap": len(train_ids & val_ids),
        "gold_holdout_overlap": len(all_ids & holdout),
        "exact_duplicate_examples": duplicates,
        "language_counts": dict(Counter(row["lang"] for row in corrective_train + corrective_val)),
        "scenario_counts": dict(Counter(row["scenario"] for row in corrective_train + corrective_val)),
    }
    (BASE / "quality_validation.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
