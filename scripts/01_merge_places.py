"""
Merges the 6 category JSON files in data/raw/ into one cleaned dataset at
data/processed/places.json, and prints coverage stats.

Usage:
    python scripts/01_merge_places.py
"""

import json
import re
from collections import Counter
from pathlib import Path

# A handful of source records have corrupted description text where
# "Kalutara" got mangled into "Kalu" followed by garbled CJK characters
# (e.g. "Kalu天涯海角..."). Restore the intended word, then strip any other
# stray CJK/Hangul/Kana runs and collapse the resulting whitespace mess.
_KALU_CJK = re.compile(r"Kalu[一-鿿぀-ヿ가-힯]+")
_CJK_RUN = re.compile(r"[一-鿿぀-ヿ가-힯]+")
_MULTISPACE = re.compile(r"\s+")


def clean_text(text: str) -> str:
    text = _KALU_CJK.sub("Kalutara", text)
    text = _CJK_RUN.sub("", text)
    text = text.replace("Kalutaratara", "Kalutara")
    return _MULTISPACE.sub(" ", text).strip()

RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"
PROCESSED_DIR = Path(__file__).resolve().parent.parent / "data" / "processed"

YES_NO_FIELDS = [
    "family_friendly",
    "parking_avail",
    "toilets",
    "food_nearby",
    "wheelchair_access",
    "camping_allowed",
    "guide_required",
    "Surfing",
]

# Source data has inconsistent spellings for the same district - canonicalize them.
DISTRICT_ALIASES = {
    "Moneragala": "Monaragala",
    "Hambantota": "Hambanthota",
    "Kurunegala": "Kurunagala",
}


def normalize_record(record: dict, source_file: str) -> dict:
    record = dict(record)
    record["source_file"] = source_file

    if "ticket_price" in record:
        try:
            record["ticket_price"] = int(float(record["ticket_price"]))
        except (TypeError, ValueError):
            record["ticket_price"] = 0

    for field in YES_NO_FIELDS:
        if field in record and isinstance(record[field], str):
            record[field] = record[field].strip().lower()

    for field in ("Height_m", "Length_km"):
        if field in record:
            try:
                record[field] = float(record[field])
            except (TypeError, ValueError):
                record[field] = 0.0

    record["description"] = clean_text(record.get("description") or "")
    record["name"] = clean_text(record.get("name") or "")

    district = (record.get("district_id") or "").strip()
    record["district_id"] = DISTRICT_ALIASES.get(district, district)

    return record


def load_items(path: Path) -> list[dict]:
    if path.suffix == ".jsonl":
        # Records may be pretty-printed across multiple lines rather than
        # strictly one JSON object per line, so decode by scanning instead
        # of splitting on newlines.
        with open(path, encoding="utf-8") as fh:
            content = fh.read()
        decoder = json.JSONDecoder()
        items = []
        idx, n = 0, len(content)
        while idx < n:
            while idx < n and content[idx].isspace():
                idx += 1
            if idx >= n:
                break
            obj, end = decoder.raw_decode(content, idx)
            items.append(obj)
            idx = end
        return items
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def main() -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    merged: dict[str, dict] = {}
    paths = sorted(RAW_DIR.glob("*.json")) + sorted(RAW_DIR.glob("*.jsonl"))
    for path in paths:
        items = load_items(path)
        for item in items:
            record = normalize_record(item, path.name)
            merged[record["id"]] = record  # last write wins on duplicate id

    places = list(merged.values())
    out_path = PROCESSED_DIR / "places.json"
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(places, fh, ensure_ascii=False, indent=2)

    print(f"Merged {len(places)} unique places -> {out_path}\n")

    print("By district:")
    for district, count in Counter(p["district_id"] for p in places).most_common():
        print(f"  {district:15s} {count}")

    print("\nBy category:")
    for cat, count in Counter(p["category_id"] for p in places).most_common(15):
        print(f"  {cat:15s} {count}")

    print("\nBy budget_category:")
    for budget, count in Counter(p["budget_category"] for p in places).most_common():
        print(f"  {budget:15s} {count}")

    print("\nData quality flags:")
    unique_coords = len({(p["lat"], p["lng"]) for p in places})
    print(f"  unique lat/lng pairs: {unique_coords} / {len(places)} places "
          f"(coordinates are likely district-level, not per-place - "
          f"don't rely on them for fine-grained distance filtering)")
    ff_values = Counter(p.get("family_friendly") for p in places)
    if len(ff_values) == 1:
        print(f"  family_friendly has a single value across all records ({ff_values}) "
              f"- not usable as a discriminating filter")
    remaining_cjk = sum(
        1 for p in places
        if _CJK_RUN.search(p["description"]) or _CJK_RUN.search(p["name"])
    )
    print(f"  records with leftover CJK contamination after cleaning: {remaining_cjk}")


if __name__ == "__main__":
    main()
