"""Generate a diverse, source-attributed, leakage-free pilot SFT draft."""

from __future__ import annotations

import hashlib
import json
import random
import re
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
PLACES = ROOT / "data" / "processed" / "part02" / "places_osm_attributed_v0.1.0.jsonl"
HOLDOUT = ROOT / "data" / "evaluation" / "gold_v0.1.0" / "holdout_place_ids.txt"
OUTPUT = ROOT / "data" / "training" / "pilot_v0.2.0"
SEED = 42
SCENARIOS = {
    "discovery": 200, "explanation": 150, "comparison": 100, "itinerary": 200,
    "family_accessibility": 100, "budget_uncertainty": 100,
    "current_fact_refusal": 100, "culture_etiquette": 50,
}
LANGUAGES = {"si": 700, "singlish": 200, "en": 100}

PREFIXES = {
    "si": ["මට උදව්වක් ලෙස", "කෙටියෙන්", "විස්තර පැහැදිලිව දක්වමින්", "අනුමාන නොකර", "ගමනක් සැලසුම් කිරීමට", "පවුලේ අයටත් තේරෙන ලෙස", "ලබාදී ඇති දත්ත අනුව", "ප්‍රායෝගිකව", "පියවරෙන් පියවර නොව කෙටියෙන්", "ශ්‍රී ලංකාවේ සංචාරයක් සඳහා"],
    "singlish": ["mata help ekak widihata", "ketiyen", "guess karanne nathuwa", "trip ekak plan karanna", "data anuwa", "practical widihata", "family ekatath therena widihata", "clear widihata", "available facts witharak aran", "travel plan ekata"],
    "en": ["Briefly", "Using only supplied facts", "Without guessing", "For a practical trip", "In a clear answer", "For a family traveler", "Based on the available context", "For planning purposes", "With uncertainty stated", "In a concise format"],
}
SUFFIXES = {
    "si": ["කියන්න.", "පැහැදිලි කරන්න.", "යෝජනාවක් දෙන්න.", "වැදගත් සීමාවන් සමඟ කියන්න.", "දත්ත නැති දේ අනුමාන නොකරන්න.", "කෙටි පිළිතුරක් දෙන්න.", "තීරණයක් ගන්න උදව් කරන්න.", "අවශ්‍ය අනතුරු ඇඟවීම් දක්වන්න.", "facts වලට සීමා වෙන්න.", "විශ්වාසදායක පිළිතුරක් දෙන්න."],
    "singlish": ["kiyanna.", "explain karanna.", "suggestion ekak denna.", "limitations ekkama kiyanna.", "data nathi de guess karanna epa.", "short answer ekak denna.", "decision ekak ganna help karanna.", "warnings thiyenawanam kiyanna.", "facts walata limit wenna.", "reliable answer ekak denna."],
    "en": ["give me an answer.", "explain it.", "make a recommendation.", "state important limitations.", "do not guess missing facts.", "keep the answer concise.", "help me decide.", "include necessary cautions.", "stay within the supplied facts.", "give a reliable response."],
}
SYSTEM = {
    "si": "ඔබ TripMe ශ්‍රී ලංකා සංචාරක සහායකයාය. ලබාදී ඇති facts පමණක් භාවිතා කරන්න. නොදන්නා current facts අනුමාන නොකරන්න.",
    "singlish": "Oba TripMe Sri Lanka travel assistant. Deela thiyena facts witharak use karanna; current facts guess karanna epa.",
    "en": "You are the TripMe Sri Lanka travel assistant. Use only supplied facts and do not guess current information.",
}


def stable(value: str) -> str:
    return hashlib.sha256(f"{SEED}|{value}".encode("utf-8")).hexdigest()


def facts(place: dict) -> str:
    activity = place.get("activities") or "not supplied"
    if isinstance(activity, list): activity = ", ".join(map(str, activity[:3]))
    return f"{place['name']} | {place['district_id']} | {place['category_id']} | activities: {activity}"


def content(lang: str, scenario: str, places: list[dict], variant: int) -> tuple[str, str]:
    a = places[0]; name, district, category = a["name"], a["district_id"], a["category_id"]
    prefix, suffix = PREFIXES[lang][variant % 10], SUFFIXES[lang][(variant // 10) % 10]
    if scenario == "discovery":
        core = {"si": f"{district} දිස්ත්‍රික්කයේ {category} ස්ථානයක් ලෙස {name} ගැන", "singlish": f"{district} district eke {category} place ekak widihata {name} gana", "en": f"tell me whether {name} is a relevant {category} option in {district}"}[lang]
        answer = {"si": f"{name} යනු {district} දිස්ත්‍රික්කයේ {category} ලෙස ලැයිස්තුගත ස්ථානයකි. ලබාදී ඇති activities: {a.get('activities') or 'සඳහන් කර නැත'}. Current conditions වෙනම තහවුරු කරන්න.", "singlish": f"{name} kiyanne {district} district eke {category} place ekak. Listed activities: {a.get('activities') or 'not supplied'}. Current conditions wenama verify karanna.", "en": f"{name} is listed as a {category} in {district}. Listed activities: {a.get('activities') or 'not supplied'}. Verify current conditions separately."}[lang]
    elif scenario == "explanation":
        core = {"si": f"{name} මොන වගේ ස්ථානයක්ද", "singlish": f"{name} mona wage place ekakda", "en": f"describe what kind of place {name} is"}[lang]
        answer = {"si": f"{name} {district} දිස්ත්‍රික්කයේ පිහිටි {category} වර්ගයේ ස්ථානයකි.", "singlish": f"{name} kiyanne {district} district eke {category} category place ekak.", "en": f"{name} is a {category} located in {district} district."}[lang]
    elif scenario == "comparison":
        b = places[1]
        core = {"si": f"{name} සහ {b['name']} අතර වෙනස", "singlish": f"{name} saha {b['name']} athara wenasa", "en": f"compare {name} with {b['name']}"}[lang]
        answer = {"si": f"{name}: {district} දිස්ත්‍රික්කයේ {category}. {b['name']}: {b['district_id']} දිස්ත්‍රික්කයේ {b['category_id']}. මිල සහ ගමන් කාලය ලබාදී නැති නිසා අනුමාන කළ නොහැක.", "singlish": f"{name}: {district}, {category}. {b['name']}: {b['district_id']}, {b['category_id']}. Prices saha travel times data nathi nisa guess karanna ba.", "en": f"{name} is a {category} in {district}; {b['name']} is a {b['category_id']} in {b['district_id']}. Prices and travel times are not supplied and should not be guessed."}[lang]
    elif scenario == "itinerary":
        joined = ", ".join(p["name"] for p in places)
        core = {"si": f"{joined} ඇතුළත් ගමන් සැලැස්මක්", "singlish": f"{joined} dala travel plan ekak", "en": f"create an itinerary containing {joined}"}[lang]
        answer = {"si": f"සැලැස්මට {joined} ඇතුළත් කළ හැක. Exact order එක තීරණය කිරීමට current opening hours සහ සැබෑ travel distances mapping source එකකින් පරීක්ෂා කරන්න.", "singlish": f"Plan ekata {joined} danna puluwan. Exact order ekata current opening hours saha real distances map source ekakin check karanna.", "en": f"The itinerary can include {joined}. Check current opening hours and real travel distances with a mapping source before fixing the order."}[lang]
    elif scenario == "family_accessibility":
        core = {"si": f"{name} පවුලකට සහ accessibility අවශ්‍ය කෙනෙකුට ගැළපේද", "singlish": f"{name} family ekakata saha accessibility needs thiyena kenekuta galapenawada", "en": f"assess family and accessibility suitability for {name}"}[lang]
        answer = {"si": f"{name} ගැන current accessibility evidence ප්‍රමාණවත් නැහැ. Entrances, toilets සහ parking ගැන ස්ථානයෙන් හෝ නිල source එකකින් තහවුරු කරන්න.", "singlish": f"{name} gana current accessibility evidence madi. Entrances, toilets saha parking official source ekakin verify karanna.", "en": f"Current accessibility evidence for {name} is insufficient. Confirm entrances, toilets and parking with the venue or an official source."}[lang]
    elif scenario in {"budget_uncertainty", "current_fact_refusal"}:
        core = {"si": f"{name} හි අද මිල සහ දැන් විවෘත තත්ත්වය", "singlish": f"{name} eke ada price eka saha dan open da kiyala", "en": f"give today's price and current opening status for {name}"}[lang]
        answer = {"si": f"Static context එකෙන් {name} හි අද මිල හෝ දැන් විවෘතද යන්න තහවුරු කළ නොහැක. Official හෝ recent dated source එකක් පරීක්ෂා කරන්න.", "singlish": f"Static context eken {name} eke ada price eka hari dan open da kiyala confirm karanna ba. Official hari recent dated source ekak check karanna.", "en": f"The static context cannot confirm today's price or whether {name} is open now. Check an official or recent dated source."}[lang]
    else:
        core = {"si": f"{name} නැරඹීමේදී ගෞරවනීය හැසිරීම", "singlish": f"{name} visit karaddi respectful behavior", "en": f"explain respectful conduct when visiting {name}"}[lang]
        answer = {"si": f"{name} හි පුවරු සහ දේශීය උපදෙස් අනුගමනය කරන්න, අන් අයට බාධා නොකරන්න, photography rules පරීක්ෂා කරන්න. විශේෂ නීති official source එකකින් තහවුරු කරන්න.", "singlish": f"{name} eke signs saha local instructions follow karanna, anith ayata disturb nokaranna, photography rules check karanna. Special rules official source ekakin verify karanna.", "en": f"At {name}, follow signs and local instructions, avoid disturbing others and check photography rules. Confirm venue-specific rules from an official source."}[lang]
    return f"{prefix} {core} {suffix}", answer


def main() -> None:
    holdout = set(HOLDOUT.read_text(encoding="utf-8").split())
    places = [json.loads(line) for line in PLACES.read_text(encoding="utf-8").splitlines() if line.strip()]
    places = sorted((p for p in places if p["id"] not in holdout), key=lambda p: stable(p["id"]))
    scenario_pool = [s for s, n in SCENARIOS.items() for _ in range(n)]
    language_pool = [l for l, n in LANGUAGES.items() for _ in range(n)]
    rng = random.Random(SEED); rng.shuffle(scenario_pool); rng.shuffle(language_pool)
    rows, cursor = [], 0
    for index, (scenario, lang) in enumerate(zip(scenario_pool, language_pool), 1):
        count = 2 if scenario == "comparison" else (3 if scenario == "itinerary" else 1)
        selected = places[cursor:cursor + count]; cursor += count
        prompt, answer = content(lang, scenario, selected, index)
        context = "\n".join(facts(p) for p in selected)
        rows.append({"lang": lang, "scenario": scenario, "place_ids": [p["id"] for p in selected], "messages": [
            {"role": "system", "content": SYSTEM[lang] + "\nContext:\n" + context},
            {"role": "user", "content": prompt}, {"role": "assistant", "content": answer}
        ]})
    train, validation = rows[:900], rows[900:]
    OUTPUT.mkdir(parents=True, exist_ok=True)
    for name, items in (("pilot_train_draft.jsonl", train), ("pilot_validation_draft.jsonl", validation)):
        with (OUTPUT / name).open("w", encoding="utf-8") as handle:
            for row in items: handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    summary = {"status": "ai_draft_requires_human_review", "train_rows": len(train), "validation_rows": len(validation), "languages": dict(Counter(r["lang"] for r in rows)), "scenarios": dict(Counter(r["scenario"] for r in rows)), "unique_place_ids": len({p for r in rows for p in r["place_ids"]}), "holdout_overlap": len({p for r in rows for p in r["place_ids"]} & holdout), "train_validation_place_overlap": len({p for r in train for p in r["place_ids"]} & {p for r in validation for p in r["place_ids"]})}
    (OUTPUT / "generation_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__": main()
