"""Build a second leakage-safe corrective set from Part 8 failure patterns."""

import json
import random
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
REGISTRY = ROOT / "data" / "registry" / "place_registry_v0.1.0.jsonl"
HOLDOUT = ROOT / "data" / "evaluation" / "gold_v0.1.0" / "holdout_place_ids.txt"
PREVIOUS = ROOT / "data" / "training" / "corrective_v0.3.0"
OUTPUT = ROOT / "data" / "training" / "corrective_v0.4.0"
SEED = 45
TRAIN_ROWS = 538
VALIDATION_ROWS = 90

SCENARIOS = (
    ["itinerary_place_retention"] * 40
    + ["family_accessibility"] * 25
    + ["culture_etiquette"] * 20
    + ["current_uncertainty"] * 10
    + ["comparison"] * 5
)
LANGUAGES = (["si"] * 60) + (["singlish"] * 20) + (["en"] * 20)


def load_jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def write_jsonl(path, rows):
    path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n", encoding="utf-8")


def render(lang, scenario, places):
    names = [place["name"] for place in places]
    facts = "\n".join(
        f"- {p['name']} | {p['district']} | {p['category']}" for p in places
    )
    if lang == "si":
        system = "ඔබ TripMe ශ්‍රී ලංකා සංචාරක සහායකයාය. ලබාදී ඇති කරුණු පමණක් භාවිතා කරන්න. ස්ථාන නාම සියල්ල පිළිතුරේ නිවැරදිව තබන්න. නොදන්නා වත්මන් තොරතුරු අනුමාන නොකරන්න.\n" + facts
        if scenario == "itinerary_place_retention":
            prompt = f"{', '.join(names)} ඇතුළත් කෙටි ගමන් සැලැස්මක් දෙන්න."
            answer = f"ගමන් සැලැස්මට පළමුව {names[0]}, දෙවනුව {names[1]}, අවසානයේ {names[2]} ඇතුළත් කළ හැක. දුර සහ ගමන් කාලය ලබාදී නැති නිසා පිටත්වීමට පෙර වත්මන් මාර්ග තොරතුරු පරීක්ෂා කරන්න."
        elif scenario == "family_accessibility":
            prompt = f"{names[0]} පවුලකට සහ රෝද පුටුවක් භාවිත කරන අයෙකුට සුදුසුද?"
            answer = f"{names[0]} හි ප්‍රවේශ පහසුකම් තහවුරු කරන දත්ත ලබාදී නැත. පවුල සමඟ යාමට පෙර පිවිසුම්, මාර්ග, වැසිකිළි සහ වාහන නැවැත්වීමේ පහසුකම් එම ස්ථානයෙන් හෝ නිල මූලාශ්‍රයකින් තහවුරු කරන්න."
        elif scenario == "culture_etiquette":
            prompt = f"{names[0]} නැරඹීමේදී අනුගමනය කළ යුතු ආචාර විධි මොනවාද?"
            answer = f"{names[0]} හි පුවරු සහ ස්ථානීය උපදෙස් අනුගමනය කර ගෞරවයෙන් හැසිරෙන්න. අනෙක් අයට බාධා නොකරන්න සහ ඡායාරූප ගැනීමට පෙර අවසර හෝ නීති පරීක්ෂා කරන්න. විශේෂ නීති එම ස්ථානයෙන් තහවුරු කරන්න."
        elif scenario == "current_uncertainty":
            prompt = f"{names[0]} අද විවෘතද සහ අද ප්‍රවේශ ගාස්තුව කීයද?"
            answer = f"ලබාදී ඇති දත්තවලින් {names[0]} අද විවෘතද හෝ අද ප්‍රවේශ ගාස්තුව කීයද යන්න තහවුරු කළ නොහැක. අනුමාන නොකර නිල හෝ මෑත දිනැති මූලාශ්‍රයකින් වත්මන් තොරතුරු පරීක්ෂා කරන්න."
        else:
            prompt = f"{names[0]} සහ {names[1]} සංසන්දනය කරන්න."
            answer = f"{names[0]} යනු {places[0]['district']} දිස්ත්‍රික්කයේ {places[0]['category']} ස්ථානයකි. {names[1]} යනු {places[1]['district']} දිස්ත්‍රික්කයේ {places[1]['category']} ස්ථානයකි. තේරීමේදී ඔබ කැමති ප්‍රදේශය සහ ක්‍රියාකාරකම් සලකා බලන්න."
    elif lang == "singlish":
        system = "Oba TripMe Sri Lanka travel assistant. Dila thiyena facts witharak use karanna. Siyalu place names answer eke hariyata thiyanna. Current details guess karanna epa.\n" + facts
        if scenario == "itinerary_place_retention":
            prompt = f"{', '.join(names)} include karala short itinerary ekak denna."
            answer = f"Itinerary eke mulin {names[0]}, deweniwata {names[1]}, anthimata {names[2]} danna puluwan. Distance saha travel time dila nathi nisa yanna kalin current route details check karanna."
        elif scenario == "family_accessibility":
            prompt = f"{names[0]} family ekakata saha wheelchair use karana kenekuta galapenawada?"
            answer = f"{names[0]} eke accessibility confirm karapu data dila naha. Family eka samaga yanna kalin entrance, path, toilet saha parking pahasukam venue eken hari official source ekakin verify karanna."
        elif scenario == "culture_etiquette":
            prompt = f"{names[0]} visit karaddi follow karanna ona etiquette mokakda?"
            answer = f"{names[0]} eke signs saha local instructions follow karala respectful widihata behave karanna. Anith ayata disturb karanna epa; photos ganna kalin permission saha rules check karanna."
        elif scenario == "current_uncertainty":
            prompt = f"{names[0]} ada open da, entrance fee eka keeyada?"
            answer = f"Dila thiyena data walin {names[0]} ada open da saha ada entrance fee eka keeyada kiyala confirm karanna ba. Guess karanne nathuwa official hari langadi date karapu source ekakin verify karanna."
        else:
            prompt = f"{names[0]} saha {names[1]} compare karanna."
            answer = f"{names[0]} kiyanne {places[0]['district']} district eke {places[0]['category']} place ekak. {names[1]} kiyanne {places[1]['district']} district eke {places[1]['category']} place ekak. Obata galapena district eka saha activity eka anuwa thoraganna."
    else:
        system = "You are the TripMe Sri Lanka travel assistant. Use only the supplied facts, retain every place name, and do not guess current information.\n" + facts
        if scenario == "itinerary_place_retention":
            prompt = f"Create a short itinerary including {', '.join(names)}."
            answer = f"A short itinerary can visit {names[0]} first, {names[1]} second, and {names[2]} last. Distances and travel times are not supplied, so check current routing information before departure."
        elif scenario == "family_accessibility":
            prompt = f"Is {names[0]} suitable for a family and a wheelchair user?"
            answer = f"The supplied facts do not confirm accessibility at {names[0]}. Before a family visit, verify entrances, paths, toilets and parking with the venue or an official source."
        elif scenario == "culture_etiquette":
            prompt = f"What etiquette should I follow when visiting {names[0]}?"
            answer = f"At {names[0]}, follow posted and local instructions, behave respectfully, avoid disturbing others, and check permission or rules before taking photographs. Confirm venue-specific rules before visiting."
        elif scenario == "current_uncertainty":
            prompt = f"Is {names[0]} open today, and what is today's entrance fee?"
            answer = f"The supplied data does not confirm whether {names[0]} is open today or its current entrance fee. Do not guess; check an official or recently dated source."
        else:
            prompt = f"Compare {names[0]} and {names[1]}."
            answer = f"{names[0]} is listed as a {places[0]['category']} in {places[0]['district']} district. {names[1]} is listed as a {places[1]['category']} in {places[1]['district']} district. Choose according to your preferred area and activity."
    return system, prompt, answer


def build(count, pool, rng, split):
    rows = []
    for index in range(count):
        scenario = SCENARIOS[index % len(SCENARIOS)]
        lang = LANGUAGES[(index * 37) % len(LANGUAGES)]
        place_count = 3 if scenario == "itinerary_place_retention" else 2 if scenario == "comparison" else 1
        places = [pool.pop() for _ in range(place_count)]
        system, prompt, answer = render(lang, scenario, places)
        rows.append({
            "lang": lang,
            "scenario": scenario,
            "place_ids": [p["canonical_place_id"] for p in places],
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
                {"role": "assistant", "content": answer},
            ],
            "review_status": "ai_corrective_draft_requires_human_review",
            "dataset_source": "part10_corrective_v0.4.0",
            "split": split,
        })
    rng.shuffle(rows)
    return rows


def main():
    rng = random.Random(SEED)
    previous_train = load_jsonl(PREVIOUS / "combined_train_ai_reviewed.jsonl")
    previous_validation = load_jsonl(PREVIOUS / "combined_validation_ai_reviewed.jsonl")
    prior_ids = {pid for row in previous_train + previous_validation for pid in row["place_ids"]}
    holdout = {line.strip() for line in HOLDOUT.read_text(encoding="utf-8").splitlines() if line.strip()}
    registry = [r for r in load_jsonl(REGISTRY) if r.get("name") and r.get("district") and r.get("category")]
    pool = [r for r in registry if r["canonical_place_id"] not in holdout | prior_ids]
    rng.shuffle(pool)
    required_places = sum(3 if s == "itinerary_place_retention" else 2 if s == "comparison" else 1 for s in [SCENARIOS[i % 100] for i in range(TRAIN_ROWS + VALIDATION_ROWS)])
    if len(pool) < required_places:
        raise ValueError(f"Need {required_places} unused places, found {len(pool)}")
    train = build(TRAIN_ROWS, pool, rng, "train")
    validation = build(VALIDATION_ROWS, pool, rng, "validation")
    train_ids = {pid for row in train for pid in row["place_ids"]}
    validation_ids = {pid for row in validation for pid in row["place_ids"]}
    assert not train_ids & validation_ids
    assert not (train_ids | validation_ids) & holdout
    combined_train = previous_train + train
    combined_validation = previous_validation + validation
    rng.shuffle(combined_train)
    rng.shuffle(combined_validation)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    write_jsonl(OUTPUT / "part10_corrective_train.jsonl", train)
    write_jsonl(OUTPUT / "part10_corrective_validation.jsonl", validation)
    write_jsonl(OUTPUT / "combined_train.jsonl", combined_train)
    write_jsonl(OUTPUT / "combined_validation.jsonl", combined_validation)
    summary = {
        "status": "ai_corrective_draft_requires_human_review",
        "seed": SEED,
        "new_train_rows": len(train),
        "new_validation_rows": len(validation),
        "combined_train_rows": len(combined_train),
        "combined_validation_rows": len(combined_validation),
        "language_counts": dict(Counter(r["lang"] for r in train + validation)),
        "scenario_counts": dict(Counter(r["scenario"] for r in train + validation)),
        "gold_holdout_overlap": 0,
        "new_train_validation_place_overlap": 0,
    }
    (OUTPUT / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
