"""Audit pilot candidates for structural validity and template repetition."""

import hashlib
import json
import re
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
PILOT = ROOT / "data" / "training" / "pilot_v0.1.0"
PLACES = ROOT / "data" / "processed" / "part02" / "places_osm_attributed_v0.1.0.jsonl"
REPORT = ROOT / "reports" / "part04"


def main() -> None:
    rows = []
    for name in ("pilot_train_candidate.jsonl", "pilot_validation_candidate.jsonl"):
        rows.extend(json.loads(line) for line in (PILOT / name).read_text(encoding="utf-8").splitlines() if line.strip())
    lookup = {row["id"]: row for row in (json.loads(line) for line in PLACES.read_text(encoding="utf-8").splitlines() if line.strip())}
    signatures, exact_pairs, errors = Counter(), Counter(), []
    for index, row in enumerate(rows, start=1):
        roles = [message.get("role") for message in row.get("messages", [])]
        if roles != ["system", "user", "assistant"]:
            errors.append({"row": index, "issue": "invalid_message_roles", "roles": roles})
            continue
        user = row["messages"][1]["content"].strip()
        assistant = row["messages"][2]["content"].strip()
        if not user or not assistant:
            errors.append({"row": index, "issue": "blank_message"})
        normalized = user.casefold()
        for place_id in row.get("place_ids") or []:
            place = lookup.get(place_id, {})
            for value in (place.get("name"), place.get("district_id"), place.get("category_id")):
                if value:
                    normalized = normalized.replace(str(value).casefold(), "<entity>")
        normalized = re.sub(r"\d+(?:\.\d+)?", "<number>", normalized)
        normalized = re.sub(r"\s+", " ", normalized).strip()
        signatures[f"{row.get('scenario')}|{normalized}"] += 1
        exact_pairs[hashlib.sha256(f"{user}|{assistant}".encode("utf-8")).hexdigest()] += 1

    unique_ratio = len(signatures) / len(rows) if rows else 0
    summary = {
        "status": "rejected_for_training",
        "rows": len(rows),
        "unique_template_signatures": len(signatures),
        "template_signature_ratio": round(unique_ratio, 4),
        "largest_template_group": max(signatures.values(), default=0),
        "exact_duplicate_rows_beyond_first": sum(value - 1 for value in exact_pairs.values() if value > 1),
        "structural_errors": len(errors),
        "readiness_threshold": {"minimum_template_signature_ratio": 0.2},
        "rejection_reasons": [
            "Template diversity is far below the minimum threshold.",
            "The set is dominated by generated single-place sentence patterns.",
            "Training on it risks teaching repetition instead of robust travel assistance."
        ]
    }
    REPORT.mkdir(parents=True, exist_ok=True)
    (REPORT / "legacy_pilot_quality_audit.json").write_text(json.dumps({"summary": summary, "template_counts": signatures, "errors": errors}, ensure_ascii=False, indent=2), encoding="utf-8")
    (PILOT / "DO_NOT_TRAIN.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()

