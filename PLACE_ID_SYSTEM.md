# TripMe Place Identification System

## Canonical identifier

Every internal reference uses `canonical_place_id`, copied from the place record's `id` field.
Example: `pl_osm_f6024a8e76`.

The `pl_osm_` text is a naming convention only. Source provenance must be determined from
`source_namespace`, `source_object_type`, `source_object_id` and `source_url`, not from the ID prefix.

## External source identifier

OpenStreetMap records retain the original object identity separately:

- `source_namespace`: `openstreetmap`
- `source_object_type`: `node`, `way` or `relation`
- `source_object_id`: original numeric OSM ID
- `source_key`: for example `osm:node:123456789`
- `source_url`: the corresponding OpenStreetMap URL

## Registry

The authoritative mapping is:

- `data/registry/place_registry_v0.1.0.jsonl`
- `data/registry/place_registry_v0.1.0.csv`

Training, evaluation and RAG relations must store `canonical_place_id`. External IDs must never
replace it, because other data providers may be added later.

