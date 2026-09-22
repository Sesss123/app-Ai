"""Finalize Roadmap Part 2 into clean, provenance-ready and quarantine sets."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
INPUT = ROOT / "data" / "verified" / "places_v0.1.0.jsonl"
OUTPUT = ROOT / "data" / "processed" / "part02"
REPORT = ROOT / "reports" / "part02_final"
REQUIRED = ("id", "name", "description", "district_id", "province_id", "category_id")
BBOX = (5.7, 10.1, 79.3, 82.1)


def write_jsonl(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    REPORT.mkdir(parents=True, exist_ok=True)
    rows = [json.loads(line) for line in INPUT.read_text(encoding="utf-8").splitlines() if line.strip()]

    accepted, provenance_ready, quarantine = [], [], []
    validation_errors = []
    seen_ids, seen_fingerprints = set(), set()
    for line_number, row in enumerate(rows, start=1):
        reasons = set(row.get("review_reasons") or [])
        for field in REQUIRED:
            if row.get(field) in (None, ""):
                reasons.add(f"missing_{field}")

        if row.get("id") in seen_ids:
            reasons.add("duplicate_id")
        if row.get("name_district_fingerprint") in seen_fingerprints:
            reasons.add("duplicate_name_district")
        seen_ids.add(row.get("id"))
        seen_fingerprints.add(row.get("name_district_fingerprint"))

        lat, lng = row.get("lat"), row.get("lng")
        if lat is None or lng is None:
            reasons.add("coordinate_review")
        elif not (BBOX[0] <= float(lat) <= BBOX[1] and BBOX[2] <= float(lng) <= BBOX[3]):
            reasons.add("coordinate_review")

        osm_type, osm_id = row.get("_osm_type"), row.get("_osm_id")
        if osm_type in {"node", "way", "relation"} and osm_id not in (None, ""):
            row["source_url"] = f"https://www.openstreetmap.org/{osm_type}/{osm_id}"
            row["source_name"] = "OpenStreetMap contributors"
            row["source_license"] = "ODbL-1.0"
            row["provenance_status"] = "source_attributed_not_fact_verified"
        else:
            row["source_url"] = None
            row["source_name"] = None
            row["source_license"] = None
            row["provenance_status"] = "missing_source_metadata"

        row["verified_at"] = None
        row["review_reasons"] = sorted(reasons)
        if reasons:
            row["data_status"] = "quarantined"
            quarantine.append(row)
        else:
            row["data_status"] = "clean_unverified"
            accepted.append(row)
            if row["provenance_status"] == "source_attributed_not_fact_verified":
                provenance_ready.append(row)

    accepted_ids = {row["id"] for row in accepted}
    quarantine_ids = {row["id"] for row in quarantine}
    if accepted_ids & quarantine_ids:
        validation_errors.append("accepted/quarantine ID overlap")
    if len(accepted) + len(quarantine) != len(rows):
        validation_errors.append("record conservation failed")

    write_jsonl(OUTPUT / "places_clean_unverified_v0.1.0.jsonl", accepted)
    write_jsonl(OUTPUT / "places_osm_attributed_v0.1.0.jsonl", provenance_ready)
    write_jsonl(OUTPUT / "places_quarantine_v0.1.0.jsonl", quarantine)

    summary = {
        "part": 2,
        "status": "complete",
        "input_records": len(rows),
        "clean_unverified_records": len(accepted),
        "osm_attributed_records": len(provenance_ready),
        "quarantined_records": len(quarantine),
        "quarantine_reason_counts": dict(Counter(reason for row in quarantine for reason in row["review_reasons"])),
        "validation_errors": validation_errors,
        "important_limitations": [
            "Clean records are structurally valid but have not been manually fact-verified.",
            "OSM attribution proves source lineage, not that every generated description or mutable field is current.",
            "Records without source metadata are not approved for training or factual RAG until license/provenance review.",
            "Prices, opening hours, safety and other mutable facts require dated live sources before user-facing use."
        ],
    }
    (REPORT / "part02_final_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    markdown = f"""# Part 2 Final Report

- Input records: **{len(rows)}**
- Clean but fact-unverified records: **{len(accepted)}**
- OSM-attributed subset: **{len(provenance_ready)}**
- Quarantined records: **{len(quarantine)}**
- Validation errors: **{len(validation_errors)}**

Part 2 technical audit and cleaning is complete. `clean_unverified` does not mean human verified.
Only the OSM-attributed subset has explicit source lineage, and mutable fields still require fresh sources.
"""
    (REPORT / "part02_final_report.md").write_text(markdown, encoding="utf-8")
    print(json.dumps(summary, indent=2))
    if validation_errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

