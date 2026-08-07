"""
Enriches data/processed/places.json descriptions with historical facts pulled
from Sri_Lanka_History_Dataset_Collector_Automated.ipynb's output
(sri_lanka_kings_validated.json / sri_lanka_events.json - kings and events
extracted from public-domain chronicle translations, keyed by `kingdom`).

Places don't carry a `kingdom` field, so this links via a KINGDOM_DISTRICTS
map (which district(s) each of the 9 historical kingdoms' territory falls in
today) - a place is only eligible if it's in a matching district AND its
category is one plausibly connected to kingdom-era history/religion
(HISTORY_ELIGIBLE_CATEGORIES: Temple, Stupa, Ruins, Devalaya, ...), never a
"district happens to equal a kingdom name" match alone - several district
names ARE kingdom names (Kandy, Anuradhapura, Kurunagala), so e.g. "Kandy
Zipline & Canopy" (an Adventure Park) sits in the right district but has
nothing to do with the Kandyan kingdom narrative; its category excludes it.
Real historical sites are typically named after the specific monument
("Ruwanwelisaya Stupa"), not the kingdom itself, so matching on the kingdom
name appearing in the place name was tried and discarded - it matched almost
nothing real. District + category is the practical signal available here;
it's still approximate (a Temple built in 1990 in Anuradhapura district gets
the same note as a 3rd-century-BC stupa), which is why only ONE short fact is
appended per place, phrased as general historical context ("Historical note:
...") rather than a claim about that specific building's own age or origin.

Usage:
    python scripts/05_enrich_with_history.py \\
        --kings sri_lanka_kings_validated.json \\
        --events sri_lanka_events.json
"""

import argparse
import json
from pathlib import Path

PROCESSED_DIR = Path(__file__).resolve().parent.parent / "data" / "processed"
PLACES_FILE = PROCESSED_DIR / "places.json"

# Which district(s) each historical kingdom's territory/capital falls in
# today, matching data/processed/places.json's district_id spelling.
KINGDOM_DISTRICTS = {
    "Anuradhapura": {"Anuradhapura"},
    "Polonnaruwa": {"Polonnaruwa"},
    "Dambadeniya": {"Kurunagala"},
    "Yapahuwa": {"Kurunagala"},
    "Kurunegala": {"Kurunagala"},
    "Gampola": {"Kandy"},
    "Kotte": {"Colombo"},
    "Sitawaka": {"Kegalle"},
    "Kandy": {"Kandy"},
}

# Categories plausibly connected to kingdom-era history/religion - the actual
# filter that keeps enrichment away from modern/unrelated places (see module
# docstring for why matching on kingdom-name-in-place-name doesn't work).
HISTORY_ELIGIBLE_CATEGORIES = {
    "Temple", "Buddhist Temple", "Kovil", "Church", "Mosque", "Devalaya",
    "Devale", "Stupa", "Ruins", "Building", "Pre-Historic Site",
    "Forest Monastery", "Cave", "Ambalama",
}


def build_district_to_kingdom() -> dict[str, str]:
    """Invert KINGDOM_DISTRICTS to district -> kingdom for lookup by place."""
    district_to_kingdom = {}
    for kingdom, districts in KINGDOM_DISTRICTS.items():
        for district in districts:
            district_to_kingdom[district] = kingdom
    return district_to_kingdom


def load_json(path: Path) -> list[dict]:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def collect_facts_by_kingdom(kings: list[dict], events: list[dict]) -> dict[str, list[str]]:
    """One short paraphrased-note fact per kingdom, confirmed/disputed only
    (legendary material is excluded - a place description shouldn't state
    legend as established history)."""
    facts: dict[str, list[str]] = {}
    for king in kings:
        kingdom = king.get("kingdom")
        note = king.get("note")
        certainty = king.get("certainty")
        if not kingdom or not note or certainty == "legendary":
            continue
        name = king.get("name", "a ruler")
        facts.setdefault(kingdom, []).append(f"{name}: {note}")
    for event in events:
        kingdom = event.get("kingdom")
        note = event.get("note")
        certainty = event.get("certainty")
        if not kingdom or not note or certainty == "legendary":
            continue
        title = event.get("title", "")
        facts.setdefault(kingdom, []).append(f"{title}: {note}" if title else note)
    return facts


def enrich(places: list[dict], facts_by_kingdom: dict[str, list[str]]) -> tuple[list[dict], int]:
    district_to_kingdom = build_district_to_kingdom()
    enriched_count = 0
    for place in places:
        if place.get("_history_enriched"):
            continue  # don't re-append facts if this script runs more than once
        if place.get("category_id") not in HISTORY_ELIGIBLE_CATEGORIES:
            continue
        district = place.get("district_id", "")
        kingdom = district_to_kingdom.get(district)
        if not kingdom:
            continue
        kingdom_facts = facts_by_kingdom.get(kingdom)
        if not kingdom_facts:
            continue
        fact = kingdom_facts[0]  # one fact per place, keeps descriptions from bloating
        place["description"] = f"{place['description']} Historical note: {fact}"
        place["_history_enriched"] = True
        place["_history_kingdom"] = kingdom
        enriched_count += 1
    return places, enriched_count


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kings", type=Path, required=True,
                         help="Path to sri_lanka_kings_validated.json")
    parser.add_argument("--events", type=Path, required=True,
                         help="Path to sri_lanka_events.json")
    args = parser.parse_args()

    places = load_json(PLACES_FILE)
    kings = load_json(args.kings)
    events = load_json(args.events)

    facts_by_kingdom = collect_facts_by_kingdom(kings, events)
    print(f"Loaded {len(kings)} kings, {len(events)} events -> "
          f"usable facts for {len(facts_by_kingdom)} kingdoms: "
          f"{sorted(facts_by_kingdom.keys())}")

    places, enriched_count = enrich(places, facts_by_kingdom)

    with open(PLACES_FILE, "w", encoding="utf-8") as fh:
        json.dump(places, fh, ensure_ascii=False, indent=2)

    print(f"Enriched {enriched_count} / {len(places)} places with a historical note.")
    print(f"Saved -> {PLACES_FILE}")


if __name__ == "__main__":
    main()
