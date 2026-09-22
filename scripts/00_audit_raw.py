"""Audit the raw travel-place files without modifying them.

The files use pretty-printed consecutive JSON objects despite the .jsonl
extension, so a normal line-by-line JSONL reader gives misleading errors.

Usage: python scripts/00_audit_raw.py
"""

import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw"
REPORT_PATH = ROOT / "data" / "processed" / "raw_audit.json"
SRI_LANKA_BBOX = (5.7, 10.1, 79.3, 82.1)
REQUIRED = ("id", "name", "description", "district_id", "province_id", "category_id", "lat", "lng")
MOJIBAKE_MARKERS = ("â€™", "â€“", "â€”", "â€œ", "â€\u009d", "ï¿½")


def load_consecutive_json(path: Path) -> list[dict]:
    text = path.read_text(encoding="utf-8-sig")
    decoder = json.JSONDecoder()
    items, index = [], 0
    while index < len(text):
        while index < len(text) and text[index].isspace():
            index += 1
        if index >= len(text):
            break
        value, index = decoder.raw_decode(text, index)
        if isinstance(value, dict):
            items.append(value)
        elif isinstance(value, list):
            items.extend(item for item in value if isinstance(item, dict))
    return items


def main() -> None:
    records = []
    parse_errors = []
    nonstandard_files = []
    for path in sorted(RAW_DIR.rglob("*.jsonl")):
        try:
            items = load_consecutive_json(path)
            records.extend((path, item) for item in items)
            first_nonempty = next((line for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()), "")
            if first_nonempty.strip() == "{":
                nonstandard_files.append(str(path.relative_to(RAW_DIR)))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            parse_errors.append({"file": str(path.relative_to(RAW_DIR)), "error": str(exc)})

    ids = Counter(str(item.get("id", "")) for _, item in records)
    names = Counter(
        (str(item.get("name", "")).strip().casefold(), str(item.get("district_id", "")).strip().casefold())
        for _, item in records
    )
    missing = Counter()
    invalid_coordinates = []
    mojibake = []
    for path, item in records:
        for field in REQUIRED:
            if item.get(field) in (None, ""):
                missing[field] += 1
        try:
            lat, lng = float(item.get("lat")), float(item.get("lng"))
            min_lat, max_lat, min_lng, max_lng = SRI_LANKA_BBOX
            if not (min_lat <= lat <= max_lat and min_lng <= lng <= max_lng):
                invalid_coordinates.append({
                    "file": str(path.relative_to(RAW_DIR)), "id": item.get("id"),
                    "name": item.get("name"), "lat": lat, "lng": lng,
                })
        except (TypeError, ValueError):
            invalid_coordinates.append({
                "file": str(path.relative_to(RAW_DIR)), "id": item.get("id"),
                "name": item.get("name"), "lat": item.get("lat"), "lng": item.get("lng"),
            })
        serialized = json.dumps(item, ensure_ascii=False)
        if any(marker in serialized for marker in MOJIBAKE_MARKERS):
            mojibake.append({"file": str(path.relative_to(RAW_DIR)), "id": item.get("id"), "name": item.get("name")})

    report = {
        "summary": {
            "files": len(list(RAW_DIR.rglob("*.jsonl"))),
            "records": len(records),
            "parse_errors": len(parse_errors),
            "pretty_printed_files_not_strict_jsonl": len(nonstandard_files),
            "duplicate_ids": sum(count - 1 for count in ids.values() if count > 1),
            "duplicate_name_district_pairs": sum(count - 1 for count in names.values() if count > 1),
            "invalid_or_unverified_coordinates": len(invalid_coordinates),
            "mojibake_records": len(mojibake),
        },
        "missing_required_fields": dict(missing),
        "parse_errors": parse_errors,
        "invalid_or_unverified_coordinates": invalid_coordinates,
        "mojibake_records": mojibake,
        "notes": [
            "Coordinates outside the bounding box are quarantined for verification, not guessed.",
            "Duplicate name+district pairs are review candidates; they are not automatically deleted.",
            "Raw source files are intentionally left unchanged.",
        ],
    }
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report["summary"], ensure_ascii=False, indent=2))
    print(f"Full report: {REPORT_PATH}")


if __name__ == "__main__":
    main()
