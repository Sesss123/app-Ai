"""
Collects Sri Lankan points of interest from OpenStreetMap (ODbL, attribution
required: "(c) OpenStreetMap contributors") via the free Overpass API, maps
them onto the places.json schema, and writes one .jsonl file per category
into data/raw/ - growing the places dataset toward ~5000.

This is the local-run counterpart to collect_osm_places.ipynb (same logic,
same bug fixes - District-suffixed area names, User-Agent header, 403/406
handling), for running on a machine without a Kaggle GPU allocation. No GPU
is used here: descriptions are always generated via the rule-based template
(see generate_description_template) since there's no local LLM step.

Resumable: progress is checkpointed to data/raw/.osm_collect_progress.json
and raw fetched elements to data/raw/.osm_raw_elements.json - re-running
after an interruption picks up where it left off.

Usage:
    python scripts/06_collect_osm_places.py
"""

import json
import random
import re
import time
import uuid
from collections import Counter, defaultdict
from pathlib import Path

import requests

RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"
PROCESSED_DIR = Path(__file__).resolve().parent.parent / "data" / "processed"
# Kept out of data/raw/ deliberately - 01_merge_places.py scans data/raw/
# recursively for *.json/*.jsonl place files, and these internal progress/
# checkpoint files are not place data (they previously caused a crash there:
# a dict-of-lists doesn't parse as a list of place records).
PROGRESS_DIR = Path(__file__).resolve().parent.parent / "data" / ".osm_progress"
PROGRESS_FILE = PROGRESS_DIR / "osm_collect_progress.json"
RAW_ELEMENTS_FILE = PROGRESS_DIR / "osm_raw_elements.json"

# Set to data/processed/places.json to dedupe against the existing dataset
# (skip OSM places that already exist there). None = dedupe only within
# this run.
EXISTING_PLACES_PATH = PROCESSED_DIR / "places.json"

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
REQUEST_DELAY = 2.0
REQUEST_TIMEOUT = 90

HTTP_SESSION = requests.Session()
HTTP_SESSION.headers.update({
    "User-Agent": "TripMeSriLankaPlacesCollector/1.0 (local run; contact: n/a)",
})

DISTRICT_PROVINCE = {
    "Colombo": "Western", "Gampaha": "Western", "Kalutara": "Western",
    "Kandy": "Central", "Matale": "Central", "Nuwara Eliya": "Central",
    "Galle": "Southern", "Matara": "Southern", "Hambanthota": "Southern",
    "Jaffna": "Northern", "Kilinochchi": "Northern", "Mannar": "Northern",
    "Vavuniya": "Northern", "Mullaitivu": "Northern",
    "Batticaloa": "Eastern", "Ampara": "Eastern", "Trincomalee": "Eastern",
    "Kurunagala": "North Western", "Puttalam": "North Western",
    "Anuradhapura": "North Central", "Polonnaruwa": "North Central",
    "Badulla": "Uva", "Monaragala": "Uva",
    "Ratnapura": "Sabaragamuwa", "Kegalle": "Sabaragamuwa",
}

OSM_DISTRICT_ALIASES = {
    "Hambantota": "Hambanthota",
    "Kurunegala": "Kurunagala",
    "Moneragala": "Monaragala",
    "Nuwara-Eliya": "Nuwara Eliya",
    "NuwaraEliya": "Nuwara Eliya",
}

# Restrict a run to specific districts (e.g. to top up under-covered
# districts without re-fetching ones that already have enough places).
# None = all districts in DISTRICT_PROVINCE.
# Currently set to the 3 districts that never got an OSM collection pass
# (Hambanthota/Kandy/Kurunagala were excluded from earlier TARGET_DISTRICTS
# runs since their place counts already looked adequate from the flat
# source-file split, but they still have no osm_*.jsonl output of their own).
TARGET_DISTRICTS = ["Hambanthota"]

# (overpass tag filter, category_id, activities hint, output filename)
OSM_CATEGORIES = [
    ('["amenity"="place_of_worship"]["religion"="buddhist"]', "Buddhist Temple", "meditation, photography", "osm_buddhist_temple.jsonl"),
    ('["amenity"="place_of_worship"]["religion"="hindu"]', "Kovil", "prayer, photography", "osm_kovil.jsonl"),
    ('["amenity"="place_of_worship"]["religion"="christian"]', "Church", "prayer, photography", "osm_church.jsonl"),
    ('["amenity"="place_of_worship"]["religion"="muslim"]', "Mosque", "prayer, photography", "osm_mosque.jsonl"),
    ('["amenity"="place_of_worship"]', "Temple", "prayer, photography", "osm_temple.jsonl"),
    ('["historic"="archaeological_site"]', "Ruins", "exploring, photography", "osm_ruins.jsonl"),
    ('["historic"="ruins"]', "Ruins", "exploring, photography", "osm_ruins.jsonl"),
    ('["historic"="monument"]', "Building", "photography, sightseeing", "osm_building.jsonl"),
    ('["historic"="memorial"]', "Building", "photography, sightseeing", "osm_building.jsonl"),
    ('["natural"="waterfall"]', "Cascade", "photography, swimming", "osm_waterfall.jsonl"),
    ('["natural"="beach"]', "Sandy Beach", "swimming, sunbathing", "osm_beach.jsonl"),
    ('["leisure"="beach_resort"]', "Sandy Beach", "swimming, relaxing", "osm_beach.jsonl"),
    ('["boundary"="national_park"]', "National Park", "wildlife watching, safari", "osm_national_park.jsonl"),
    ('["leisure"="nature_reserve"]', "National Park", "wildlife watching, hiking", "osm_national_park.jsonl"),
    ('["tourism"="viewpoint"]', "Viewpoint", "photography, sightseeing", "osm_viewpoint.jsonl"),
    ('["tourism"="museum"]', "Museum", "sightseeing, learning", "osm_museum.jsonl"),
    ('["tourism"="zoo"]', "Adventure Park", "wildlife watching", "osm_adventure_park.jsonl"),
    ('["tourism"="theme_park"]', "Adventure Park", "rides, family fun", "osm_adventure_park.jsonl"),
    ('["landuse"="farmland"]["crop"="tea"]', "Tea Estate", "walking, photography", "osm_tea_estate.jsonl"),
    ('["tourism"="attraction"]', "Other", "sightseeing", "osm_other.jsonl"),
]

CATEGORY_BLURB = {
    "Buddhist Temple": "a Buddhist temple", "Kovil": "a Hindu kovil", "Church": "a church",
    "Mosque": "a mosque", "Temple": "a place of worship", "Ruins": "an archaeological site",
    "Building": "a historic landmark", "Cascade": "a waterfall", "Sandy Beach": "a beach",
    "National Park": "a nature reserve", "Viewpoint": "a scenic viewpoint", "Museum": "a museum",
    "Adventure Park": "an attraction", "Tea Estate": "a tea estate", "Other": "a point of interest",
}

OPENER_TEMPLATES = [
    "{name} is {blurb} located in {district}, Sri Lanka.",
    "{name} is {blurb} in the {district} area of Sri Lanka.",
    "Located in {district}, {name} is {blurb} worth visiting.",
]

CLOSER_TEMPLATES = {
    "Buddhist Temple": "Visitors can explore the temple grounds and take part in quiet reflection.",
    "Kovil": "Visitors are welcome to observe the shrine's architecture and rituals respectfully.",
    "Church": "The site offers a peaceful stop for visitors interested in local religious heritage.",
    "Mosque": "Visitors are welcome to view the architecture from outside prayer times.",
    "Temple": "It offers visitors a glimpse into local religious life.",
    "Ruins": "The site offers insight into the region's historical past for visitors interested in archaeology.",
    "Building": "It stands as a marker of the area's local history.",
    "Cascade": "Visitors can enjoy the surrounding scenery and, where safe, a refreshing dip.",
    "Sandy Beach": "It's a good spot for swimming, relaxing, and watching the sunset.",
    "National Park": "Visitors can look out for local wildlife while exploring the area.",
    "Viewpoint": "It offers a scenic spot to pause and take in the surrounding views.",
    "Museum": "It offers visitors a chance to learn more about local history and culture.",
    "Adventure Park": "It's a popular spot for a family day out.",
    "Tea Estate": "Visitors can enjoy views of the tea plantations and surrounding hills.",
    "Other": "It's worth a stop for travelers exploring the area.",
}


def generate_description_template(name: str, category_id: str, district: str) -> str:
    blurb = CATEGORY_BLURB.get(category_id, "a point of interest")
    opener = random.choice(OPENER_TEMPLATES).format(name=name, blurb=blurb, district=district)
    closer = CLOSER_TEMPLATES.get(category_id, CLOSER_TEMPLATES["Other"])
    return f"{opener} {closer}"


DEFAULT_FIELDS = {
    "opening_hours": "Check locally", "mobile_signal": "Moderate", "road_condition": "Paved",
    "tourist_popularity": "Low", "family_friendly": "yes", "budget_category": "Free",
    "ticket_price": 0, "parking_avail": "unknown", "toilets": "unknown", "food_nearby": "unknown",
    "wheelchair_access": "unknown", "camping_allowed": "no", "safety_level": "Safe",
    "wildlife_hazard": "None", "guide_required": "no", "rain_sensitivity": "Caution",
    "monsoon_note": "Avoid May-Sept", "best_time_to_visit": "Dec to Mar",
    "Height_m": 0.0, "Length_km": 0.0, "Surfing": "no",
}

CATEGORY_OVERRIDES = {
    "National Park": {"wildlife_hazard": "Present - stay in vehicle/with guide", "guide_required": "yes"},
    "Sandy Beach": {"budget_category": "Free"},
    "Museum": {"budget_category": "Low"},
    "Tea Estate": {"budget_category": "Low"},
}


_OUR_TO_OSM_DISTRICT_SPELLING = {v: k for k, v in OSM_DISTRICT_ALIASES.items()}


def build_query(district: str, tag_filter: str) -> str:
    # OSM's admin boundary relation for a Sri Lankan district is tagged
    # name:en="<District> District" (confirmed via Nominatim/Overpass for
    # every district). Filtering on the plain "name" tag instead is
    # unreliable: for most districts name == name:en so it happens to
    # work, but some districts (e.g. Kurunegala, whose "name" tag is the
    # transliterated "Kurunǣgala" with no "District" suffix) have a
    # completely different plain "name" value, so area["name"="Kurunegala
    # District"] silently matches nothing. Also our internal spelling can
    # differ from OSM's English spelling (our "Hambanthota" vs OSM's
    # "Hambantota", our "Kurunagala" vs OSM's "Kurunegala") - translate
    # back to OSM's spelling before building the name:en filter.
    osm_district = _OUR_TO_OSM_DISTRICT_SPELLING.get(district, district)
    area_name = f"{osm_district} District"
    return f"""
    [out:json][timeout:{REQUEST_TIMEOUT}];
    area["name"="Sri Lanka"]->.country;
    area["name:en"="{area_name}"](area.country)->.searchArea;
    (
      node{tag_filter}(area.searchArea);
      way{tag_filter}(area.searchArea);
    );
    out center tags 200;
    """


def overpass_fetch(query: str, retries: int = 3) -> list:
    for attempt in range(retries):
        try:
            r = HTTP_SESSION.post(OVERPASS_URL, data={"data": query}, timeout=REQUEST_TIMEOUT)
            if r.status_code == 200:
                try:
                    return r.json().get("elements", [])
                except ValueError:
                    print(f"  non-JSON 200 response (attempt {attempt+1}), retrying...")
                    time.sleep(10 * (attempt + 1))
                    continue
            if r.status_code in (429, 504):
                time.sleep(10 * (attempt + 1))
                continue
            if r.status_code == 406:
                print(f"  406 Not Acceptable (attempt {attempt+1}) - check the User-Agent "
                      "header is still set, retrying...")
                time.sleep(5 * (attempt + 1))
                continue
            if r.status_code == 403:
                print(f"  403 Forbidden (attempt {attempt+1}) - possible IP-based block, retrying...")
                time.sleep(15 * (attempt + 1))
                continue
            r.raise_for_status()
        except requests.RequestException as e:
            print(f"  request failed (attempt {attempt+1}): {e}")
            time.sleep(5 * (attempt + 1))
    print("  giving up on this query after retries - returning 0 elements for it.")
    return []


def load_progress() -> dict:
    if PROGRESS_FILE.exists():
        return json.loads(PROGRESS_FILE.read_text(encoding="utf-8"))
    return {"completed": []}


def save_progress(progress: dict) -> None:
    PROGRESS_FILE.write_text(json.dumps(progress, indent=2), encoding="utf-8")


def load_existing_ids(path: Path) -> set:
    ids = set()
    text = path.read_text(encoding="utf-8")
    decoder = json.JSONDecoder()
    idx = 0
    n = len(text)
    while idx < n:
        while idx < n and text[idx] in " \t\r\n":
            idx += 1
        if idx >= n:
            break
        obj, end = decoder.raw_decode(text, idx)
        if isinstance(obj, dict) and "id" in obj:
            ids.add(obj["id"])
        idx = end
    return ids


def norm_name(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", (name or "").lower())


def osm_center(el: dict):
    if el["type"] == "node":
        return el.get("lat"), el.get("lon")
    center = el.get("center") or {}
    return center.get("lat"), center.get("lon")


def make_record(el: dict) -> dict | None:
    tags = el.get("tags", {})
    name = (tags.get("name:en") or tags.get("name") or "").strip()
    if not name:
        return None

    lat, lng = osm_center(el)
    if lat is None or lng is None:
        return None

    district = OSM_DISTRICT_ALIASES.get(el["_district"], el["_district"])
    category_id = el["_category_id"]

    record = {
        "id": f"pl_osm_{uuid.uuid4().hex[:10]}",
        "name": name,
        "description": generate_description_template(name, category_id, district),
        "district_id": district,
        "province_id": DISTRICT_PROVINCE[district],
        "category_id": category_id,
        "lat": round(float(lat), 6),
        "lng": round(float(lng), 6),
        "activities": el["_activities"],
        "_osm_type": el["type"],
        "_osm_id": el["id"],
        "_source_global_id": str(uuid.uuid4()),
    }
    defaults = dict(DEFAULT_FIELDS)
    defaults.update(CATEGORY_OVERRIDES.get(category_id, {}))
    for k, v in defaults.items():
        record[k] = v
    record["_output_file"] = el["_output_file"]
    return record


def haversine_m(lat1, lon1, lat2, lon2) -> float:
    import math
    R = 6371000
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlambda / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROGRESS_DIR.mkdir(parents=True, exist_ok=True)

    existing_places = []
    if EXISTING_PLACES_PATH and EXISTING_PLACES_PATH.exists():
        existing_places = json.loads(EXISTING_PLACES_PATH.read_text(encoding="utf-8"))
    existing_by_norm_name: dict = {}
    for p in existing_places:
        existing_by_norm_name.setdefault(norm_name(p["name"]), []).append(p)
    print(f"Loaded {len(existing_places)} existing places for dedup.")

    progress = load_progress()
    raw_osm_elements = []
    if RAW_ELEMENTS_FILE.exists():
        raw_osm_elements = json.loads(RAW_ELEMENTS_FILE.read_text(encoding="utf-8"))
    print(f"Resuming: {len(progress['completed'])} (district, category) pairs already done, "
          f"{len(raw_osm_elements)} raw elements already fetched.")

    target_districts = TARGET_DISTRICTS if TARGET_DISTRICTS is not None else list(DISTRICT_PROVINCE)
    pairs = [(d, cat, filt, act, fn) for d in target_districts for (filt, cat, act, fn) in OSM_CATEGORIES]
    print(f"Targeting {len(target_districts)} district(s): {target_districts}")
    failed_pairs = []
    for idx, (district, category_id, tag_filter, activities, output_file) in enumerate(pairs, 1):
        key = f"{district}::{category_id}::{tag_filter}"
        if key in progress["completed"]:
            continue
        print(f"[{idx}/{len(pairs)}] {district} / {category_id}...")
        try:
            query = build_query(district, tag_filter)
            elements = overpass_fetch(query)
        except Exception as e:
            print(f"  UNEXPECTED error for {key}: {e} - skipping this pair.")
            failed_pairs.append(key)
            elements = []
        for el in elements:
            el["_district"] = district
            el["_category_id"] = category_id
            el["_activities"] = activities
            el["_output_file"] = output_file
            raw_osm_elements.append(el)
        progress["completed"].append(key)
        RAW_ELEMENTS_FILE.write_text(json.dumps(raw_osm_elements), encoding="utf-8")
        save_progress(progress)
        time.sleep(REQUEST_DELAY)

    print(f"\nFetched {len(raw_osm_elements)} raw OSM elements across "
          f"{len(DISTRICT_PROVINCE)} districts x {len(OSM_CATEGORIES)} category filters.")
    if failed_pairs:
        print(f"{len(failed_pairs)} pairs hit an unexpected error: {failed_pairs}")

    # Convert -> dedupe -> save
    candidate_records = []
    seen_osm_ids = set()
    for el in raw_osm_elements:
        osm_key = (el["type"], el["id"])
        if osm_key in seen_osm_ids:
            continue
        seen_osm_ids.add(osm_key)
        rec = make_record(el)
        if rec:
            candidate_records.append(rec)
    print(f"{len(candidate_records)} candidate records built from {len(raw_osm_elements)} raw elements.")

    def is_duplicate(record: dict) -> bool:
        candidates = existing_by_norm_name.get(norm_name(record["name"]), [])
        for existing in candidates:
            if haversine_m(record["lat"], record["lng"], existing["lat"], existing["lng"]) <= 300:
                return True
        return False

    deduped_records = []
    seen_in_run = set()
    dropped_existing = 0
    dropped_within_run = 0
    for rec in candidate_records:
        if is_duplicate(rec):
            dropped_existing += 1
            continue
        run_key = (norm_name(rec["name"]), round(rec["lat"], 3), round(rec["lng"], 3))
        if run_key in seen_in_run:
            dropped_within_run += 1
            continue
        seen_in_run.add(run_key)
        deduped_records.append(rec)

    print(f"Kept {len(deduped_records)} records.")
    print(f"Dropped {dropped_existing} as duplicates of existing places.json entries.")
    print(f"Dropped {dropped_within_run} as duplicates within this run.")

    # Grouped by (district, category filename) so output lands at
    # data/raw/{district}/{category}.jsonl - one folder per district, one
    # file per category within it.
    by_district_file: dict = defaultdict(list)
    for rec in deduped_records:
        rec = dict(rec)
        output_file = rec.pop("_output_file")
        by_district_file[(rec["district_id"], output_file)].append(rec)

    saved_files = []
    for (district, output_file), records in sorted(by_district_file.items()):
        district_dir = RAW_DIR / district
        district_dir.mkdir(parents=True, exist_ok=True)
        out_path = district_dir / output_file
        # Append, not overwrite - this file may already hold records saved
        # by an earlier run (e.g. a previous TARGET_DISTRICTS pass), and
        # opening in "w" mode would silently discard them.
        existing_ids = load_existing_ids(out_path) if out_path.exists() else set()
        new_records = [r for r in records if r["id"] not in existing_ids]
        if new_records:
            with open(out_path, "a", encoding="utf-8") as f:
                for rec in new_records:
                    f.write(json.dumps(rec, indent=4, ensure_ascii=False))
                    f.write("\n\n")
        saved_files.append((district, output_file, len(new_records)))
        print(f"Saved {len(new_records):4d} new places (+{len(records) - len(new_records)} already present) -> {out_path}")

    print(f"\nTotal: {sum(n for _, _, n in saved_files)} places across {len(saved_files)} district/category files.")
    print("\nBy district:")
    for d, c in Counter(r["district_id"] for r in deduped_records).most_common():
        print(f"  {d:15s} {c}")
    print("\nNext step: python scripts/01_merge_places.py")
    print('\nAttribution: this data includes OpenStreetMap content - cite '
          '"(c) OpenStreetMap contributors" (ODbL) wherever this dataset is published.')


if __name__ == "__main__":
    main()
