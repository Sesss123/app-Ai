"""Create an AI-assisted draft batch for human authoring and review.

The output is intentionally marked as a draft and must never be treated as a
gold set until a human author edits it and an independent reviewer approves it.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
GOLD_DIR = ROOT / "data" / "evaluation" / "gold_v0.1.0"


def activities_text(place: dict) -> str:
    value = place.get("activities")
    if isinstance(value, list):
        return ", ".join(str(item) for item in value[:4]) or "not supplied"
    return str(value or "not supplied")


def make_draft(row: dict, places: list[dict]) -> tuple[str, str, list[str]]:
    lang, scenario = row["language"], row["scenario"]
    first = places[0]
    name, district, category = first["name"], first["district_id"], first["category_id"]
    acts = activities_text(first)
    facts = [f"{name} — district: {district}", f"{name} — category: {category}"]

    if scenario == "place_discovery":
        prompts = {
            "si": f"{district} දිස්ත්‍රික්කයේ {category} වර්ගයේ බලන්න හොඳ ස්ථානයක් යෝජනා කරන්න.",
            "singlish": f"{district} district eke balanna honda {category} place ekak suggest karanna.",
            "en": f"Suggest a {category} place to visit in {district} district."
        }
        answers = {
            "si": f"{district} දිස්ත්‍රික්කයේ {category} ස්ථානයක් ලෙස {name} සලකා බලන්න. ලබාදී ඇති දත්ත අනුව එහි සඳහන් ක්‍රියාකාරකම්: {acts}. යාමට පෙර විවෘත වේලාවන් සහ වත්මන් තත්ත්වය අලුත් මූලාශ්‍රයකින් තහවුරු කරන්න.",
            "singlish": f"{district} district eke {category} place ekak widihata {name} balanna puluwan. Data eke activities lesa {acts} sandahan wenawa. Yanna kalin opening hours saha current status aluth source ekakin verify karanna.",
            "en": f"Consider {name}, listed as a {category} in {district} district. Its supplied activities are: {acts}. Verify opening hours and current conditions from a fresh source before visiting."
        }
    elif scenario == "place_explanation":
        prompts = {"si": f"{name} කියන්නේ මොන වගේ ස්ථානයක්ද?", "singlish": f"{name} kiyanne mona wage place ekakda?", "en": f"What kind of place is {name}?"}
        answers = {"si": f"{name} යනු {district} දිස්ත්‍රික්කයේ ඇති {category} වර්ගයට අයත් ස්ථානයකි. දත්තවල සඳහන් ක්‍රියාකාරකම්: {acts}.", "singlish": f"{name} kiyanne {district} district eke {category} category ekata ayath place ekak. Data eke activities: {acts}.", "en": f"{name} is listed as a {category} in {district} district. The supplied activities are: {acts}."}
    elif scenario == "comparison":
        second = places[1]
        facts.extend([f"{second['name']} — district: {second['district_id']}", f"{second['name']} — category: {second['category_id']}"])
        prompts = {"si": f"{name} සහ {second['name']} සංසන්දනය කරන්න.", "singlish": f"{name} saha {second['name']} compare karanna.", "en": f"Compare {name} and {second['name']}."}
        answers = {"si": f"{name} යනු {district} දිස්ත්‍රික්කයේ {category} ස්ථානයකි. {second['name']} යනු {second['district_id']} දිස්ත්‍රික්කයේ {second['category_id']} ස්ථානයකි. තෝරාගැනීමේදී ඔබ කැමති ප්‍රදේශය සහ ක්‍රියාකාරකම් සලකා බලන්න; ලබාදී නැති මිල හෝ ගමන් කාලය අනුමාන කළ නොහැක.", "singlish": f"{name} kiyanne {district} district eke {category} place ekak. {second['name']} kiyanne {second['district_id']} district eke {second['category_id']} place ekak. Data nathi prices saha travel times guess karanna ba.", "en": f"{name} is a {category} in {district}; {second['name']} is a {second['category_id']} in {second['district_id']}. Choose based on your preferred area and activities; prices and travel times not supplied should not be guessed."}
    elif scenario == "itinerary":
        names = [place["name"] for place in places]
        facts.extend(f"{place['name']} — {place['district_id']} / {place['category_id']}" for place in places[1:])
        joined = ", ".join(names)
        prompts = {"si": f"{joined} ඇතුළත් කෙටි සංචාර සැලැස්මක් හදන්න.", "singlish": f"{joined} dala short travel plan ekak hadanna.", "en": f"Create a short itinerary including {joined}."}
        answers = {"si": f"සැලැස්මට {joined} ඇතුළත් කළ හැක. නිශ්චිත අනුපිළිවෙළ තීරණය කිරීමට පෙර ස්ථානවල වත්මන් විවෘත වේලාවන් සහ සැබෑ ගමන් දුර map/routing source එකකින් පරීක්ෂා කරන්න.", "singlish": f"Plan ekata {joined} danna puluwan. Exact order eka hadanna kalin current opening hours saha travel distance map source ekakin check karanna.", "en": f"The plan can include {joined}. Before fixing the order, check current opening hours and actual travel distances with a mapping or routing source."}
    elif scenario == "family_accessibility":
        prompts = {"si": f"{name} පවුලක් සමඟ හෝ wheelchair එකක් භාවිත කරන කෙනෙකුට සුදුසුද?", "singlish": f"{name} family ekakata hari wheelchair use karana kenekuta hari suitable da?", "en": f"Is {name} suitable for a family or a wheelchair user?"}
        answers = {"si": f"{name} හි family සහ wheelchair suitability ගැන current, independently verified තොරතුරු මෙහි ප්‍රමාණවත් නැහැ. පිවිසුම් මාර්ග, වැසිකිළි සහ parking ගැන ස්ථානයෙන් හෝ නිල මූලාශ්‍රයකින් කලින් තහවුරු කරන්න.", "singlish": f"{name} eke family saha wheelchair suitability gana verified current data madi. Entrance, toilets saha parking official source ekakin kalin check karanna.", "en": f"The supplied context is not enough to confirm current family or wheelchair suitability at {name}. Check entrances, toilets and parking with the venue or an official source before visiting."}
    elif scenario in {"uncertainty_current", "budget"}:
        prompts = {"si": f"{name} දැන් විවෘතද සහ අද ticket price එක කීයද?", "singlish": f"{name} dan open da, ada ticket price eka kiyada?", "en": f"Is {name} open now, and what is today's ticket price?"}
        answers = {"si": f"{name} හි වත්මන් විවෘත තත්ත්වය හෝ අද ticket price එක මෙම static data වලින් තහවුරු කළ නොහැක. නිල හෝ අලුත් dated source එකක් පරීක්ෂා කරන්න.", "singlish": f"{name} dan open da saha ada ticket price eka me static data walin confirm karanna ba. Official hari aluth dated source ekak check karanna.", "en": f"The static context cannot confirm whether {name} is open now or today's ticket price. Check an official or recent dated source."}
    elif scenario == "false_premise_refusal":
        wrong = next(value for value in ("Colombo", "Kandy", "Galle", "Jaffna") if value != district)
        prompts = {"si": f"{name} {wrong} දිස්ත්‍රික්කයේ තියෙන නිසා එතැනට යන විදිහ කියන්න.", "singlish": f"{name} {wrong} district eke nisa yanna widihak kiyanna.", "en": f"Since {name} is in {wrong} district, tell me how to get there."}
        answers = {"si": f"ප්‍රශ්නයේ district එක නිවැරදි නැහැ. ලබාදී ඇති දත්ත අනුව {name} පිහිටා තිබෙන්නේ {district} දිස්ත්‍රික්කයේය. නිශ්චිත මාර්ගයක් සඳහා current mapping service එකක් භාවිත කරන්න.", "singlish": f"Question eke district eka waradi. Data anuwa {name} thiyenne {district} district eke. Exact route ekata current map service ekak use karanna.", "en": f"The district in the question is incorrect. The supplied data places {name} in {district} district. Use a current mapping service for exact directions."}
    else:
        prompts = {"si": f"{name} නැරඹීමේදී ගෞරවනීයව හැසිරීමට මතක තබාගත යුතු දේ මොනවාද?", "singlish": f"{name} visit karaddi respectful widihata inna mathaka thiyaganna ona de monawada?", "en": f"What should I remember to behave respectfully when visiting {name}?"}
        answers = {"si": f"{name} හි දේශීය උපදෙස් සහ පුවරු අනුගමනය කරන්න, අනෙකුත් අයට බාධා නොකරන්න, ඡායාරූප ගැනීමට පෙර අවසර අවශ්‍යද බලන්න. ස්ථානයට විශේෂ dress හෝ conduct rules තිබේ නම් ඒවා නිල මූලාශ්‍රයකින් තහවුරු කරන්න.", "singlish": f"{name} eke local signs saha instructions follow karanna, anith ayata disturb nokaranna, photos ganna kalin permission ona da balanna. Special rules official source ekakin check karanna.", "en": f"Follow local signs and instructions at {name}, avoid disturbing others, and check whether photography needs permission. Confirm any venue-specific dress or conduct rules from an official source."}
    return prompts[lang], answers[lang], facts


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", type=int, default=1)
    parser.add_argument("--count", type=int, default=50)
    args = parser.parse_args()
    scaffold = [json.loads(line) for line in (GOLD_DIR / "gold_scaffold.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    lookup = {row["id"]: row for row in (json.loads(line) for line in (GOLD_DIR / "holdout_places.jsonl").read_text(encoding="utf-8").splitlines() if line.strip())}
    selected = scaffold[args.start - 1:args.start - 1 + args.count]
    drafts = []
    for row in selected:
        draft = dict(row)
        prompt, answer, facts = make_draft(row, [lookup[value] for value in row["target_place_ids"]])
        draft.update({"prompt": prompt, "reference_answer": answer, "required_facts": facts, "author_id": "codex_ai_draft", "review_status": "ai_draft_needs_human_author_and_reviewer"})
        drafts.append(draft)
    end = args.start + len(drafts) - 1
    stem = f"gold_batch_{args.start:03d}_{end:03d}_draft"
    jsonl_path = GOLD_DIR / f"{stem}.jsonl"
    with jsonl_path.open("w", encoding="utf-8") as handle:
        for row in drafts:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    with (GOLD_DIR / f"{stem}.csv").open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(drafts[0]))
        writer.writeheader()
        for row in drafts:
            item = dict(row)
            for key, value in item.items():
                if isinstance(value, list):
                    item[key] = json.dumps(value, ensure_ascii=False)
            writer.writerow(item)
    print(f"Created {len(drafts)} AI-assisted drafts: {jsonl_path}")


if __name__ == "__main__":
    main()
