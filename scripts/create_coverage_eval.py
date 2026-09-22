"""Generate the 10,000-item automated Part 3B coverage evaluation set.

This is not a human gold set. Each row contains deterministic checks that can
be scored automatically against a model or RAG response.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from itertools import cycle
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SPEC_PATH = ROOT / "config" / "coverage_eval_spec.json"
PLACES_PATH = ROOT / "data" / "processed" / "part02" / "places_osm_attributed_v0.1.0.jsonl"
OUTPUT = ROOT / "data" / "evaluation" / "coverage_v0.1.0"


TEMPLATES = {
    "place_identity": {
        "si": "{name} ගැන dataset එකේ තිබෙන තොරතුරු පමණක් භාවිතයෙන් කෙටියෙන් කියන්න.",
        "singlish": "{name} gana dataset eke thiyena thorathuru witharak use karala kiyanna.",
        "en": "Briefly describe {name} using only the supplied dataset context."
    },
    "district_grounding": {
        "si": "{name} පිහිටා තිබෙන්නේ කුමන දිස්ත්‍රික්කයේද?",
        "singlish": "{name} thiyenne mona district ekeda?",
        "en": "Which district is {name} located in?"
    },
    "category_grounding": {
        "si": "{name} අයත් වන සංචාරක ස්ථාන වර්ගය කුමක්ද?",
        "singlish": "{name} mona place category ekakata ayathda?",
        "en": "What place category does {name} belong to?"
    },
    "activity_grounding": {
        "si": "{name} හි කළ හැකි ක්‍රියාකාරකම් ගැන දන්නා දේ කියන්න.",
        "singlish": "{name} eke karanna puluwan activities monawada?",
        "en": "What activities are listed for {name}?"
    },
    "recommendation": {
        "si": "{district} දිස්ත්‍රික්කයේ {category} ස්ථානයක් යෝජනා කරන්න.",
        "singlish": "{district} district eke {category} place ekak suggest karanna.",
        "en": "Suggest a {category} place in {district} district."
    },
    "comparison": {
        "si": "{name} සහ {other_name} dataset facts අනුව සසඳන්න.",
        "singlish": "{name} saha {other_name} dataset facts anuwa compare karanna.",
        "en": "Compare {name} and {other_name} using only the supplied facts."
    },
    "missing_current_fact": {
        "si": "{name} දැන් විවෘතද සහ අද ticket price එක කීයද?",
        "singlish": "{name} dan open da, ada ticket price eka kiyada?",
        "en": "Is {name} open now, and what is today's ticket price?"
    },
    "false_premise": {
        "si": "{name} {wrong_district} දිස්ත්‍රික්කයේ තිබෙන නිසා එහි යන මාර්ගය කියන්න.",
        "singlish": "{name} {wrong_district} district eke nisa yanna para kiyanna.",
        "en": "Since {name} is in {wrong_district} district, tell me how to get there."
    }
}


def stable_key(value: str, seed: int) -> str:
    return hashlib.sha256(f"{seed}|{value}".encode("utf-8")).hexdigest()


def main() -> None:
    spec = json.loads(SPEC_PATH.read_text(encoding="utf-8"))
    places = [json.loads(line) for line in PLACES_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]
    places.sort(key=lambda row: stable_key(str(row["id"]), spec["seed"]))
    districts = sorted({row["district_id"] for row in places})
    scenario_pool = [scenario for scenario, count in spec["scenarios"].items() for _ in range(count)]
    language_pool = [language for _ in range(spec["total_prompts"] // 4) for language in ("si", "singlish", "si", "en")]
    place_iter = cycle(places)
    rows = []
    for index, scenario in enumerate(scenario_pool, start=1):
        place = next(place_iter)
        other = next(place_iter) if scenario == "comparison" else None
        wrong_district = next(value for value in districts if value != place["district_id"])
        language = language_pool[index - 1]
        prompt = TEMPLATES[scenario][language].format(
            name=place["name"], district=place["district_id"], category=place["category_id"],
            other_name=other["name"] if other else "", wrong_district=wrong_district
        )
        context_ids = [place["id"]] + ([other["id"]] if other else [])
        expected = {
            "correct_name": place["name"],
            "correct_district": place["district_id"],
            "correct_category": place["category_id"],
            "must_acknowledge_missing_current_data": scenario == "missing_current_fact",
            "must_correct_false_premise": scenario == "false_premise",
            "must_not_invent_current_price_hours_or_safety": True
        }
        rows.append({
            "eval_id": f"coverage-{index:05d}", "language": language, "scenario": scenario,
            "prompt": prompt, "context_place_ids": context_ids, "expected_checks": expected,
            "source_urls": [place["source_url"]] + ([other["source_url"]] if other else [])
        })
    OUTPUT.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT / "coverage_eval_10000.jsonl"
    with output_path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    summary = {
        "status": "complete",
        "type": "automated_coverage_not_human_gold",
        "rows": len(rows),
        "unique_primary_places": len({row["context_place_ids"][0] for row in rows}),
        "language_counts": dict(Counter(row["language"] for row in rows)),
        "scenario_counts": dict(Counter(row["scenario"] for row in rows)),
        "source_dataset": str(PLACES_PATH.relative_to(ROOT)).replace("\\", "/")
    }
    (OUTPUT / "coverage_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()

