"""Validate the generated v0.2.0 pilot draft and enforce quality gates."""

import json
import re
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
BASE = ROOT / "data" / "training" / "pilot_v0.2.0"
PLACES = ROOT / "data" / "processed" / "part02" / "places_osm_attributed_v0.1.0.jsonl"
HOLDOUT = set((ROOT / "data" / "evaluation" / "gold_v0.1.0" / "holdout_place_ids.txt").read_text(encoding="utf-8").split())


def main() -> None:
    train = [json.loads(x) for x in (BASE / "pilot_train_draft.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
    val = [json.loads(x) for x in (BASE / "pilot_validation_draft.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
    rows = train + val
    lookup = {r["id"]: r for r in (json.loads(x) for x in PLACES.read_text(encoding="utf-8").splitlines() if x.strip())}
    signatures = set(); errors = []
    for i, row in enumerate(rows, 1):
        if [m.get("role") for m in row.get("messages", [])] != ["system", "user", "assistant"]:
            errors.append(f"row {i}: roles")
            continue
        prompt = row["messages"][1]["content"].casefold()
        for pid in row["place_ids"]:
            for value in (lookup[pid]["name"], lookup[pid]["district_id"], lookup[pid]["category_id"]):
                prompt = prompt.replace(str(value).casefold(), "<entity>")
        prompt = re.sub(r"\d+(?:\.\d+)?", "<number>", prompt)
        signatures.add(f"{row['lang']}|{row['scenario']}|{prompt}")
    train_ids = {p for r in train for p in r["place_ids"]}; val_ids = {p for r in val for p in r["place_ids"]}
    summary = {
        "rows": len(rows), "train_rows": len(train), "validation_rows": len(val),
        "unique_template_signatures": len(signatures),
        "template_signature_ratio": round(len(signatures) / len(rows), 4),
        "holdout_overlap": len((train_ids | val_ids) & HOLDOUT),
        "train_validation_place_overlap": len(train_ids & val_ids),
        "language_counts": dict(Counter(r["lang"] for r in rows)),
        "scenario_counts": dict(Counter(r["scenario"] for r in rows)),
        "structural_errors": errors,
    }
    passed = len(rows) == 1000 and len(train) == 900 and len(val) == 100 and summary["template_signature_ratio"] >= 0.2 and not summary["holdout_overlap"] and not summary["train_validation_place_overlap"] and not errors
    summary["automated_quality_gate"] = "passed" if passed else "failed"
    (BASE / "quality_validation.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    if not passed: raise SystemExit(1)


if __name__ == "__main__": main()
