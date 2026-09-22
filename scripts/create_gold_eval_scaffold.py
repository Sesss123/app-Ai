"""Create the Part 3 holdout and human-authoring scaffold."""

from __future__ import annotations

import csv
import hashlib
import json
import random
from itertools import cycle
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SPEC_PATH = ROOT / "config" / "gold_eval_spec.json"
PLACES_PATH = ROOT / "data" / "processed" / "part02" / "places_osm_attributed_v0.1.0.jsonl"
OUTPUT = ROOT / "data" / "evaluation" / "gold_v0.1.0"


SCENARIO_BRIEFS = {
    "place_discovery": "Ask for suitable places using district, category, activity, or preference constraints.",
    "place_explanation": "Ask what the selected place is and why a traveler may visit it.",
    "comparison": "Compare the selected places only on facts present in the supplied context.",
    "budget": "Ask a budget-sensitive question; do not assume a current price when it is not verified.",
    "itinerary": "Request a practical short itinerary using the selected places without inventing travel times.",
    "family_accessibility": "Ask about family or accessibility needs and expose missing evidence clearly.",
    "uncertainty_current": "Ask about a mutable fact such as current opening, price, weather, road, or safety status.",
    "false_premise_refusal": "Include an unsupported or false premise that the assistant should correct or decline.",
    "culture_etiquette": "Ask for respectful conduct at a religious or cultural place without stereotyping.",
}


def stable_key(record: dict, seed: int) -> str:
    return hashlib.sha256(f"{seed}|{record['id']}".encode("utf-8")).hexdigest()


def write_jsonl(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def main() -> None:
    spec = json.loads(SPEC_PATH.read_text(encoding="utf-8"))
    places = [json.loads(line) for line in PLACES_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]
    places.sort(key=lambda row: stable_key(row, spec["seed"]))
    OUTPUT.mkdir(parents=True, exist_ok=True)

    # Repeating this four-item block gives the locked 2:1:1 distribution
    # while spreading languages across every scenario block.
    blocks = spec["total_prompts"] // 4
    language_pool = [language for _ in range(blocks) for language in ("si", "singlish", "si", "en")]

    scenarios = []
    for scenario, count in spec["scenarios"].items():
        scenarios.extend([scenario] * count)
    random.Random(spec["seed"]).shuffle(scenarios)

    assignments, selected_places = [], {}
    place_iter = cycle(places)
    for index, scenario in enumerate(scenarios, start=1):
        target_count = 2 if scenario == "comparison" else (3 if scenario == "itinerary" else 1)
        targets = []
        while len(targets) < target_count:
            place = next(place_iter)
            if place["id"] not in {item["id"] for item in targets}:
                targets.append(place)
                selected_places[place["id"]] = place
        assignments.append({
            "eval_id": f"gold-{index:03d}",
            "language": language_pool[index - 1],
            "scenario": scenario,
            "target_place_ids": [item["id"] for item in targets],
            "target_place_names": [item["name"] for item in targets],
            "districts": sorted({item["district_id"] for item in targets}),
            "author_brief": SCENARIO_BRIEFS[scenario],
            "prompt": "",
            "reference_answer": "",
            "required_facts": [],
            "forbidden_claims": ["invented current facts", "unsupported safety guarantee"],
            "author_id": "",
            "reviewer_id": "",
            "review_status": "unwritten"
        })

    fieldnames = list(assignments[0].keys())
    with (OUTPUT / "gold_authoring_sheet.csv").open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in assignments:
            csv_row = dict(row)
            for key in ("target_place_ids", "target_place_names", "districts", "required_facts", "forbidden_claims"):
                csv_row[key] = json.dumps(csv_row[key], ensure_ascii=False)
            writer.writerow(csv_row)

    write_jsonl(OUTPUT / "gold_scaffold.jsonl", assignments)
    holdout_rows = list(selected_places.values())
    write_jsonl(OUTPUT / "holdout_places.jsonl", holdout_rows)
    (OUTPUT / "holdout_place_ids.txt").write_text(
        "\n".join(sorted(selected_places)) + "\n", encoding="utf-8"
    )
    training_place_ids = set()
    for training_file in (ROOT / "data" / "training").glob("*.jsonl"):
        for line in training_file.read_text(encoding="utf-8").splitlines():
            if line.strip():
                training_place_ids.update(json.loads(line).get("place_ids") or [])
    overlap = sorted(set(selected_places) & training_place_ids)
    (OUTPUT / "training_exclusion_required_ids.txt").write_text(
        "\n".join(overlap) + ("\n" if overlap else ""), encoding="utf-8"
    )
    summary = {
        "status": "scaffold_created_not_gold_approved",
        "assignments": len(assignments),
        "holdout_places": len(holdout_rows),
        "language_counts": spec["languages"],
        "scenario_counts": spec["scenarios"],
        "current_training_place_overlap": len(overlap),
        "leakage_action": "Part 4 must regenerate/filter all training splits using training_exclusion_required_ids.txt.",
        "warning": "Prompts and reference answers must be written and approved by human reviewers before this becomes a gold set."
    }
    (OUTPUT / "scaffold_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
