"""
Validates data/training/train.jsonl and val.jsonl before they're used for
fine-tuning: structural correctness, groundedness against places.json, and
basic text-quality checks (encoding, length).

Usage:
    python scripts/03_validate_dataset.py
"""

import json
import re
from pathlib import Path

PROCESSED_DIR = Path(__file__).resolve().parent.parent / "data" / "processed"
TRAINING_DIR = Path(__file__).resolve().parent.parent / "data" / "training"

CJK_RUN = re.compile(r"[一-鿿぀-ヿ가-힯]+")


def load_jsonl(path: Path) -> list:
    examples = []
    with open(path, encoding="utf-8") as fh:
        for line_no, line in enumerate(fh, 1):
            line = line.strip()
            if not line:
                continue
            try:
                examples.append(json.loads(line))
            except json.JSONDecodeError as e:
                raise SystemExit(f"{path}:{line_no}: invalid JSON - {e}")
    return examples


def validate_file(path: Path, places_by_id: dict) -> dict:
    examples = load_jsonl(path)
    issues = []

    empty_responses = 0
    contradictions = 0
    cjk_leftover = 0
    unknown_place_ids = 0
    token_lengths = []

    for i, ex in enumerate(examples):
        messages = ex.get("messages", [])
        if len(messages) != 3 or [m["role"] for m in messages] != ["system", "user", "assistant"]:
            issues.append(f"example {i}: unexpected message structure")
            continue

        assistant_text = messages[2]["content"]
        if not assistant_text.strip():
            empty_responses += 1
            continue

        if CJK_RUN.search(assistant_text):
            cjk_leftover += 1

        token_lengths.append(len(assistant_text.split()))

        place_ids = ex.get("place_ids", [])
        referenced_places = []
        for pid in place_ids:
            place = places_by_id.get(pid)
            if place is None:
                unknown_place_ids += 1
            else:
                referenced_places.append(place)

        # Spot-check: if every referenced place is marked unsafe/dangerous,
        # the response shouldn't claim it's generally safe (checked for
        # both the English and Sinhala "generally safe" phrasing).
        safe_claims = ("generally safe", "සාමාන්‍යයෙන් ආරක්ෂිත")
        for place in referenced_places:
            safety = str(place.get("safety_level", "")).lower()
            if "danger" in safety and any(c in assistant_text.lower() for c in safe_claims):
                contradictions += 1
                break

    return {
        "file": path.name,
        "count": len(examples),
        "empty_responses": empty_responses,
        "cjk_leftover": cjk_leftover,
        "unknown_place_ids": unknown_place_ids,
        "contradictions": contradictions,
        "token_lengths": token_lengths,
    }


def print_report(report: dict) -> None:
    lengths = report["token_lengths"]
    print(f"{report['file']}: {report['count']} examples")
    print(f"  empty responses:        {report['empty_responses']}")
    print(f"  CJK/foreign contamination: {report['cjk_leftover']}")
    print(f"  unknown place_ids:       {report['unknown_place_ids']}")
    print(f"  safety contradictions:   {report['contradictions']}")
    if lengths:
        lengths_sorted = sorted(lengths)
        n = len(lengths_sorted)
        p50 = lengths_sorted[n // 2]
        p95 = lengths_sorted[int(n * 0.95)]
        print(f"  response length (words): min={min(lengths)} p50={p50} p95={p95} max={max(lengths)}")
    print()


def main() -> None:
    with open(PROCESSED_DIR / "places.json", encoding="utf-8") as fh:
        places = json.load(fh)
    places_by_id = {p["id"]: p for p in places}

    any_failures = False
    filenames = ("train.jsonl", "val.jsonl", "train_si.jsonl", "val_si.jsonl")
    for filename in filenames:
        path = TRAINING_DIR / filename
        if not path.exists():
            print(f"(skipping {filename} - not found)\n")
            continue
        report = validate_file(path, places_by_id)
        print_report(report)
        if report["empty_responses"] or report["cjk_leftover"] or report["unknown_place_ids"] or report["contradictions"]:
            any_failures = True

    if any_failures:
        raise SystemExit("Validation found issues - see report above.")
    print("All checks passed.")


if __name__ == "__main__":
    main()
