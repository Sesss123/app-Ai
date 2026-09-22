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

# Deliberately broad bounding box used only to reject impossible coordinates.
# Rejected values are preserved in source_lat/source_lng for later human review.
SRI_LANKA_BBOX = (5.7, 10.1, 79.3, 82.1)


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

    try:
        lat = float(record.get("lat"))
        lng = float(record.get("lng"))
        min_lat, max_lat, min_lng, max_lng = SRI_LANKA_BBOX
        coordinate_is_possible = min_lat <= lat <= max_lat and min_lng <= lng <= max_lng
    except (TypeError, ValueError):
        lat, lng, coordinate_is_possible = record.get("lat"), record.get("lng"), False

    if coordinate_is_possible:
        record["lat"], record["lng"] = lat, lng
        record["coordinate_status"] = "unverified"
    else:
        record["source_lat"], record["source_lng"] = lat, lng
        record["lat"], record["lng"] = None, None
        record["coordinate_status"] = "needs_review"

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
    # rglob (not glob) so files inside district subfolders
    # (data/raw/{district}/{category}.jsonl, written by
    # 06_collect_osm_places.py) are picked up alongside the flat top-level
    # category files.
    paths = sorted(RAW_DIR.rglob("*.json")) + sorted(RAW_DIR.rglob("*.jsonl"))
    for path in paths:
        items = load_items(path)
        if not isinstance(items, list):
            # A non-place JSON file (e.g. a stray checkpoint/config file
            # that ended up under data/raw/) - skip it rather than crashing
            # the whole merge on a dict-of-lists or other unexpected shape.
            print(f"  skipping {path} - not a JSON list of place records")
            continue
        # relative_to(RAW_DIR) instead of path.name so files in different
        # district subfolders sharing a basename (e.g. Kandy/osm_temple.jsonl
        # and Galle/osm_temple.jsonl) still get distinct source_file values.
        source_label = str(path.relative_to(RAW_DIR))
        for item in items:
            if not isinstance(item, dict):
                # Avoid printing the full value: a stray nested dataset can be
                # huge and may contain characters unsupported by the terminal.
                print(f"  skipping non-dict item in {path} ({type(item).__name__})")
                continue
            record = normalize_record(item, source_label)
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
    valid_places = [p for p in places if p.get("coordinate_status") != "needs_review"]
    unique_coords = len({(p["lat"], p["lng"]) for p in valid_places})
    print(f"  unique lat/lng pairs: {unique_coords} / {len(places)} places "
          f"(coordinates are likely district-level, not per-place - "
          f"don't rely on them for fine-grained distance filtering)")
    print(f"  coordinates needing review: {len(places) - len(valid_places)}")
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
