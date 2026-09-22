"""Create a canonical, non-destructive cleaned place dataset.

Raw files are never modified. Impossible coordinates are set to null and
queued for review. Name/district duplicates are flagged, not auto-deleted.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path


BBOX = (5.7, 10.1, 79.3, 82.1)
REQUIRED = ("id", "name", "description", "district_id", "province_id", "category_id")
DISTRICT_ALIASES = {"Moneragala": "Monaragala", "Hambantota": "Hambanthota", "Kurunegala": "Kurunagala"}
SPACE_RE = re.compile(r"\s+")


def load_consecutive_json(path: Path) -> list[dict]:
    text = path.read_text(encoding="utf-8-sig")
    decoder, items, index = json.JSONDecoder(), [], 0
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


def clean_text(value: object) -> str:
    return SPACE_RE.sub(" ", str(value or "")).strip()


def normalize(record: dict, source_file: str) -> tuple[dict, list[str]]:
    item = dict(record)
    issues: list[str] = []
    item["name"] = clean_text(item.get("name"))
    item["description"] = clean_text(item.get("description"))
    district = clean_text(item.get("district_id"))
    item["district_id"] = DISTRICT_ALIASES.get(district, district)
    item["source_file"] = source_file.replace("\\", "/")
    item["data_status"] = "needs_review"

    for field in REQUIRED:
        if item.get(field) in (None, ""):
            issues.append(f"missing_{field}")

    try:
        lat, lng = float(item.get("lat")), float(item.get("lng"))
        min_lat, max_lat, min_lng, max_lng = BBOX
        valid_coordinate = min_lat <= lat <= max_lat and min_lng <= lng <= max_lng
    except (TypeError, ValueError):
        lat, lng, valid_coordinate = item.get("lat"), item.get("lng"), False

    if valid_coordinate:
        item["lat"], item["lng"] = lat, lng
        item["coordinate_status"] = "unverified"
    else:
        item["source_lat"], item["source_lng"] = lat, lng
        item["lat"], item["lng"] = None, None
        item["coordinate_status"] = "needs_review"
        issues.append("coordinate_review")

    fingerprint_source = "|".join((item["name"].casefold(), item["district_id"].casefold()))
    item["name_district_fingerprint"] = hashlib.sha256(fingerprint_source.encode("utf-8")).hexdigest()[:16]
    if not issues:
        item["data_status"] = "candidate"
    return item, issues


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    records: list[dict] = []
    issues_by_index: dict[int, list[str]] = defaultdict(list)
    parse_errors = []
    for path in sorted(args.raw_dir.rglob("*.jsonl")):
        try:
            source = path.relative_to(args.raw_dir).as_posix()
            for source_record in load_consecutive_json(path):
                item, issues = normalize(source_record, source)
                index = len(records)
                records.append(item)
                issues_by_index[index].extend(issues)
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            parse_errors.append({"source_file": str(path), "issue": "parse_error", "detail": str(exc)})

    id_groups: dict[str, list[int]] = defaultdict(list)
    name_groups: dict[str, list[int]] = defaultdict(list)
    for index, item in enumerate(records):
        id_groups[str(item.get("id", ""))].append(index)
        name_groups[item["name_district_fingerprint"]].append(index)
    for indexes in id_groups.values():
        if len(indexes) > 1:
            for index in indexes:
                issues_by_index[index].append("duplicate_id")
    for indexes in name_groups.values():
        if len(indexes) > 1:
            for index in indexes:
                issues_by_index[index].append("duplicate_name_district")

    review_rows = []
    for index, item in enumerate(records):
        issues = sorted(set(issues_by_index[index]))
        item["review_reasons"] = issues
        if issues:
            item["data_status"] = "needs_review"
            review_rows.append({
                "id": item.get("id"), "name": item.get("name"),
                "district": item.get("district_id"), "source_file": item.get("source_file"),
                "issues": ";".join(issues), "source_lat": item.get("source_lat", item.get("lat")),
                "source_lng": item.get("source_lng", item.get("lng")),
            })

    with (args.output_dir / "places_clean.jsonl").open("w", encoding="utf-8") as handle:
        for item in records:
            handle.write(json.dumps(item, ensure_ascii=False) + "\n")
    with (args.output_dir / "manual_review_queue.csv").open("w", newline="", encoding="utf-8-sig") as handle:
        fields = ["id", "name", "district", "source_file", "issues", "source_lat", "source_lng"]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(review_rows)

    summary = {
        "raw_files": len(list(args.raw_dir.rglob("*.jsonl"))),
        "records": len(records),
        "candidate_records": sum(item["data_status"] == "candidate" for item in records),
        "records_needing_review": len(review_rows),
        "invalid_coordinates": sum("coordinate_review" in row["issues"] for row in review_rows),
        "duplicate_id_records": sum("duplicate_id" in row["issues"] for row in review_rows),
        "duplicate_name_district_records": sum("duplicate_name_district" in row["issues"] for row in review_rows),
        "parse_errors": len(parse_errors),
        "issue_counts": dict(Counter(issue for issues in issues_by_index.values() for issue in set(issues))),
    }
    (args.output_dir / "cleaning_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (args.output_dir / "parse_errors.json").write_text(json.dumps(parse_errors, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()

