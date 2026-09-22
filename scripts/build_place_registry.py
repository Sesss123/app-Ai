"""Build and validate the canonical TripMe place-ID registry."""

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "data" / "processed" / "part02" / "places_osm_attributed_v0.1.0.jsonl"
OUTPUT = ROOT / "data" / "registry"


def main() -> None:
    rows = [json.loads(line) for line in SOURCE.read_text(encoding="utf-8").splitlines() if line.strip()]
    registry, seen = [], set()
    for row in rows:
        canonical_id = str(row["id"])
        if canonical_id in seen:
            raise SystemExit(f"Duplicate canonical ID: {canonical_id}")
        seen.add(canonical_id)
        osm_type, osm_id = row.get("_osm_type"), row.get("_osm_id")
        source_key = f"osm:{osm_type}:{osm_id}"
        registry.append({
            "canonical_place_id": canonical_id,
            "source_namespace": "openstreetmap",
            "source_object_type": osm_type,
            "source_object_id": str(osm_id),
            "source_key": source_key,
            "source_url": row["source_url"],
            "name": row["name"],
            "district": row["district_id"],
            "category": row["category_id"],
            "registry_status": "active_unverified"
        })
    OUTPUT.mkdir(parents=True, exist_ok=True)
    with (OUTPUT / "place_registry_v0.1.0.jsonl").open("w", encoding="utf-8") as handle:
        for row in registry:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    with (OUTPUT / "place_registry_v0.1.0.csv").open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(registry[0]))
        writer.writeheader(); writer.writerows(registry)
    summary = {"records": len(registry), "unique_canonical_ids": len(seen), "duplicate_canonical_ids": 0}
    (OUTPUT / "registry_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()

