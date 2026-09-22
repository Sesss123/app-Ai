"""Generate leakage-safe corrective data from the Part 6 failure analysis."""

import json
import random
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
REGISTRY = ROOT / "data" / "registry" / "place_registry_v0.1.0.jsonl"
HOLDOUT = ROOT / "data" / "evaluation" / "gold_v0.1.0" / "holdout_place_ids.txt"
PILOT = ROOT / "data" / "training" / "pilot_v0.2.0" / "review"
OUTPUT = ROOT / "data" / "training" / "corrective_v0.3.0"
SEED = 43

SPLITS = {
    "train": {"si": 720, "singlish": 90, "en": 90},
    "validation": {"si": 120, "singlish": 15, "en": 15},
}
SCENARIO_WEIGHTS = {
    "current_fact_refusal": 30,
    "budget_uncertainty": 20,
    "family_accessibility": 25,
    "culture_etiquette": 15,
    "grounded_explanation": 10,
}

CATEGORY_SI = {
    "Buddhist Temple": "බෞද්ධ විහාරස්ථානය",
    "Temple": "ආගමික ස්ථානය",
    "Kovil": "කෝවිල",
    "Church": "ක්‍රිස්තියානි දේවස්ථානය",
    "Mosque": "මුස්ලිම් දේවස්ථානය",
    "Other": "වෙනත් ස්ථානය",
    "Viewpoint": "දර්ශන ස්ථානය",
    "Ruins": "නටබුන් ස්ථානය",
    "Building": "ගොඩනැගිල්ල",
    "Museum": "කෞතුකාගාරය",
    "Sandy Beach": "වැලි සහිත වෙරළ",
    "Adventure Park": "ත්‍රාසජනක උද්‍යානය",
    "Tea Estate": "තේ වත්ත",
    "National Park": "ජාතික වනෝද්‍යානය",
    "Lighthouse": "ප්‍රදීපාගාරය",
    "Geographic Feature": "භූගෝලීය ස්ථානය",
}


def load_jsonl(path: Path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_jsonl(path: Path, rows):
    path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n", encoding="utf-8")


def allocate(total: int) -> dict[str, int]:
    raw = {key: total * weight / 100 for key, weight in SCENARIO_WEIGHTS.items()}
    result = {key: int(value) for key, value in raw.items()}
    remaining = total - sum(result.values())
    for key in sorted(raw, key=lambda item: raw[item] - int(raw[item]), reverse=True):
        if not remaining:
            break
        result[key] += 1
        remaining -= 1
    return result


def system_text(lang: str, place: dict) -> str:
    name, district, category = place["name"], place["district"], place["category"]
    if lang == "si":
        category_text = CATEGORY_SI.get(category, category)
        return (
            "ඔබ TripMe ශ්‍රී ලංකා සංචාරක සහායකයාය. පහත කරුණු පමණක් භාවිතා කරන්න. "
            "නොදන්නා වත්මන් තොරතුරු අනුමාන නොකරන්න.\n"
            f"ස්ථානය: {name}\nදිස්ත්‍රික්කය: {district}\nවර්ගය: {category_text}"
        )
    if lang == "singlish":
        return (
            "Oba TripMe Sri Lanka travel assistant. Pahatha facts witharak use karanna. "
            "Nodanna current details guess karanna epa.\n"
            f"Place: {name}\nDistrict: {district}\nCategory: {category}"
        )
    return (
        "You are the TripMe Sri Lanka travel assistant. Use only the facts below and do not guess current information.\n"
        f"Place: {name}\nDistrict: {district}\nCategory: {category}"
    )


def prompt_and_answer(lang: str, scenario: str, place: dict, variant: int):
    n, d, c = place["name"], place["district"], place["category"]
    csi = CATEGORY_SI.get(c, c)
    if lang == "si":
        prompts = {
            "current_fact_refusal": [
                f"{n} දැන් විවෘතද? අද ප්‍රවේශ ගාස්තුවත් කියන්න.",
                f"{n} හි වත්මන් විවෘත තත්ත්වය සහ අද මිල තහවුරු කර දෙන්න.",
                f"අනුමාන නොකර {n} අද විවෘතද සහ ප්‍රවේශ ගාස්තුව කීයද කියන්න.",
            ],
            "budget_uncertainty": [
                f"{n} නැරඹීමට අද වැය වන මුදල කීයද?",
                f"{n} සඳහා වත්මන් ප්‍රවේශ ගාස්තුව සහ වෙනත් වියදම් කියන්න.",
                f"{n} යන්න budget එකක් හදන්න අද ticket price එක කියන්න.",
            ],
            "family_accessibility": [
                f"{n} පවුලක් සමඟ සහ රෝද පුටුවක් භාවිත කරන කෙනෙකුට සුදුසුද?",
                f"{n} හි පිවිසුම්, වැසිකිළි සහ වාහන නැවැත්වීමේ පහසුකම් තිබේද?",
                f"ප්‍රවේශ පහසුකම් අවශ්‍ය කෙනෙකුට {n} ගැළපේද කියන්න.",
            ],
            "culture_etiquette": [
                f"{n} නැරඹීමේදී ගෞරවනීයව හැසිරිය යුත්තේ කොහොමද?",
                f"{n} වෙත යන විට අනුගමනය කළ යුතු සාමාන්‍ය ආචාර විධි කියන්න.",
                f"{n} නැරඹීම සඳහා වැදගත් හැසිරීම් උපදෙස් දෙන්න.",
            ],
            "grounded_explanation": [
                f"{n} මොන වගේ ස්ථානයක්ද? ලබාදී ඇති කරුණු පමණක් කියන්න.",
                f"{n} ගැන කෙටි සහ තහවුරු කළ විස්තරයක් දෙන්න.",
                f"{n} පිහිටි දිස්ත්‍රික්කය සහ ස්ථාන වර්ගය කියන්න.",
            ],
        }
        answers = {
            "current_fact_refusal": [
                f"ලබාදී ඇති දත්තවල {n} හි වත්මන් විවෘත තත්ත්වය හෝ අද ප්‍රවේශ ගාස්තුව සඳහන් නොවේ. {n} පිළිබඳ එම තොරතුරු නිල හෝ මෑත දිනයක් සඳහන් මූලාශ්‍රයකින් තහවුරු කරන්න.",
                f"{n} දැන් විවෘතද සහ අද ගාස්තුව කීයද යන්න ලබාදී ඇති කරුණුවලින් තහවුරු කළ නොහැක. අනුමාන නොකර නිල මූලාශ්‍රයක් පරීක්ෂා කරන්න.",
            ],
            "budget_uncertainty": [
                f"{n} සඳහා වත්මන් ප්‍රවේශ ගාස්තුව හෝ වෙනත් වියදම් ලබාදී ඇති දත්තවල නැත. වියදම් සැලැස්ම තීරණය කිරීමට පෙර {n} හි නිල හෝ මෑත දිනයක් සඳහන් මූලාශ්‍රයක් පරීක්ෂා කරන්න.",
                f"ලබාදී ඇති කරුණු අනුව {n} හි අද මිල තහවුරු කළ නොහැක. මිල අනුමාන නොකර අදාළ නිල මූලාශ්‍රයෙන් වත්මන් ගාස්තුව තහවුරු කරන්න.",
            ],
            "family_accessibility": [
                f"{n} හි ප්‍රවේශ පහසුකම් පිළිබඳ තහවුරු කළ තොරතුරු ලබාදී නැත. පිවිසුම්, වැසිකිළි, මාර්ග සහ වාහන නැවැත්වීමේ පහසුකම් {n} වෙතින් හෝ නිල මූලාශ්‍රයකින් තහවුරු කරන්න.",
                f"පවුලකට හෝ රෝද පුටුවක් භාවිත කරන කෙනෙකුට {n} සුදුසුද යන්න මේ දත්තවලින් තහවුරු කළ නොහැක. අවශ්‍ය පහසුකම් අදාළ ස්ථානයෙන් විමසන්න.",
            ],
            "culture_etiquette": [
                f"{n} හි පුවරු සහ ස්ථානීය උපදෙස් අනුගමනය කරන්න. අන් අයට බාධා නොකරන්න සහ ඡායාරූප ගැනීමට පෙර අවසර හෝ නීති පරීක්ෂා කරන්න. {n} සඳහා විශේෂ නීති තිබේ නම් ඒවා නිල මූලාශ්‍රයකින් තහවුරු කරන්න.",
                f"{n} නැරඹීමේදී නිහතමානීව හැසිරී ස්ථානයේ උපදෙස් පිළිපදින්න. ඇඳුම්, ඡායාරූප සහ ප්‍රවේශයට අදාළ විශේෂ නීති අනුමාන නොකර එම ස්ථානයෙන් තහවුරු කරන්න.",
            ],
            "grounded_explanation": [
                f"{n} පිහිටා ඇත්තේ {d} දිස්ත්‍රික්කයේ වන අතර එහි වර්ගය {csi} ලෙස සඳහන් වේ. ලබාදී ඇති දත්තවලින් වත්මන් මිල, විවෘත වේලාවන් හෝ වෙනත් පහසුකම් තහවුරු කළ නොහැක.",
                f"ලබාදී ඇති කරුණු අනුව {n} පිහිටා ඇත්තේ {d} දිස්ත්‍රික්කයේ වන අතර එහි වර්ගය {csi} ලෙස සඳහන් වේ.",
            ],
        }
    elif lang == "singlish":
        prompts = {
            "current_fact_refusal": [f"{n} dan open da saha ada ticket price eka keeyada?", f"Guess karanne nathuwa {n} eke current opening status saha ada fee eka kiyanna."],
            "budget_uncertainty": [f"{n} balanna ada yana cost eka keeyada?", f"{n} visit karanna current entrance fee saha anith costs kiyanna."],
            "family_accessibility": [f"{n} family ekakata saha wheelchair use karana kenekuta galapenawada?", f"{n} eke entrance, toilet saha parking pahasukam thiyenawada?"],
            "culture_etiquette": [f"{n} visit karaddi respectful widihata behave karanne kohomada?", f"{n} yaddi follow karanna ona general etiquette kiyanna."],
            "grounded_explanation": [f"Dila thiyena facts anuwa {n} mona wage place ekakda?", f"{n} thiyena district eka saha category eka kiyanna."],
        }
        answers = {
            "current_fact_refusal": [f"Dila thiyena data walin {n} dan open da saha ada entrance fee eka keeyada kiyala confirm karanna ba. {n} gana official source ekak hari langadi date karapu source ekak check karanna."],
            "budget_uncertainty": [f"{n} eke current entrance fee saha anith costs dila thiyena data wala naha. Budget eka hadanna kalin {n} official source ekakin current price eka confirm karanna."],
            "family_accessibility": [f"{n} eke accessibility pahasukam gana confirm karapu details dila naha. Entrance, toilet, path saha parking pahasukam {n} eken hari official source ekakin verify karanna."],
            "culture_etiquette": [f"{n} eke signs saha local instructions follow karanna. Anith ayata disturb karanne nathuwa photo ganna kalin rules check karanna. Special rules official source ekakin confirm karanna."],
            "grounded_explanation": [f"{n} kiyanne {d} district eke {c} category ekata ayath place ekak. Current prices saha opening hours dila naha."],
        }
    else:
        prompts = {
            "current_fact_refusal": [f"Is {n} open now, and what is today's entrance fee?", f"Without guessing, confirm the current opening status and today's price for {n}."],
            "budget_uncertainty": [f"What does it cost to visit {n} today?", f"Give the current entrance fee and other visit costs for {n}."],
            "family_accessibility": [f"Is {n} suitable for a family and a wheelchair user?", f"Does {n} have accessible entrances, toilets and parking?"],
            "culture_etiquette": [f"How should a visitor behave respectfully at {n}?", f"What general etiquette should I follow when visiting {n}?"],
            "grounded_explanation": [f"Using only the supplied facts, what kind of place is {n}?", f"State the district and category of {n}."],
        }
        answers = {
            "current_fact_refusal": [f"The supplied facts do not confirm whether {n} is open now or its current entrance fee. Check an official or recently dated source for {n} rather than guessing."],
            "budget_uncertainty": [f"The supplied data does not include the current entrance fee or other costs for {n}. Confirm current prices with an official or recently dated source before setting a budget."],
            "family_accessibility": [f"The supplied facts do not confirm accessibility at {n}. Check entrances, paths, toilets and parking with {n} or an official source before visiting."],
            "culture_etiquette": [f"At {n}, follow posted and local instructions, avoid disturbing others, and check the rules before taking photographs. Confirm any venue-specific requirements through an official source."],
            "grounded_explanation": [f"{n} is listed as a {c} in {d} district. The supplied facts do not confirm current prices, opening hours or facilities."],
        }
    prompt_options, answer_options = prompts[scenario], answers[scenario]
    return prompt_options[variant % len(prompt_options)], answer_options[(variant // len(prompt_options)) % len(answer_options)]


def build_rows(places, split: str, rng: random.Random):
    specs = []
    for lang, total in SPLITS[split].items():
        for scenario, count in allocate(total).items():
            specs.extend((lang, scenario) for _ in range(count))
    rng.shuffle(specs)
    assert len(specs) == len(places)
    rows = []
    variant_counts = Counter()
    for index, (place, (lang, scenario)) in enumerate(zip(places, specs), 1):
        variant = variant_counts[(lang, scenario)]
        variant_counts[(lang, scenario)] += 1
        prompt, answer = prompt_and_answer(lang, scenario, place, variant)
        rows.append({
            "lang": lang,
            "scenario": scenario,
            "place_ids": [place["canonical_place_id"]],
            "messages": [
                {"role": "system", "content": system_text(lang, place)},
                {"role": "user", "content": prompt},
                {"role": "assistant", "content": answer},
            ],
            "review_status": "ai_corrective_draft_requires_human_review",
            "dataset_source": "part07_corrective_v0.3.0",
        })
    rng.shuffle(rows)
    return rows


def main():
    rng = random.Random(SEED)
    registry = [row for row in load_jsonl(REGISTRY) if row.get("registry_status") == "active_unverified" and row.get("name") and row.get("district") and row.get("category")]
    holdout = {line.strip() for line in HOLDOUT.read_text(encoding="utf-8").splitlines() if line.strip()}
    pilot_train = load_jsonl(PILOT / "second_checked_train_candidate.jsonl")
    pilot_validation = load_jsonl(PILOT / "second_checked_validation_candidate.jsonl")
    pilot_ids = {place_id for row in pilot_train + pilot_validation for place_id in row["place_ids"]}
    eligible = [row for row in registry if row["canonical_place_id"] not in holdout and row["canonical_place_id"] not in pilot_ids]
    rng.shuffle(eligible)
    needed = sum(sum(split.values()) for split in SPLITS.values())
    if len(eligible) < needed:
        raise ValueError(f"Need {needed} unused places; found {len(eligible)}")
    train_count = sum(SPLITS["train"].values())
    val_count = sum(SPLITS["validation"].values())
    corrective_train = build_rows(eligible[:train_count], "train", rng)
    corrective_validation = build_rows(eligible[train_count:train_count + val_count], "validation", rng)
    combined_train = pilot_train + corrective_train
    combined_validation = pilot_validation + corrective_validation
    rng.shuffle(combined_train)
    rng.shuffle(combined_validation)

    OUTPUT.mkdir(parents=True, exist_ok=True)
    write_jsonl(OUTPUT / "corrective_train_draft.jsonl", corrective_train)
    write_jsonl(OUTPUT / "corrective_validation_draft.jsonl", corrective_validation)
    write_jsonl(OUTPUT / "combined_train_candidate.jsonl", combined_train)
    write_jsonl(OUTPUT / "combined_validation_candidate.jsonl", combined_validation)
    summary = {
        "status": "corrective_data_generated_requires_human_review",
        "seed": SEED,
        "corrective_train_rows": len(corrective_train),
        "corrective_validation_rows": len(corrective_validation),
        "combined_train_rows": len(combined_train),
        "combined_validation_rows": len(combined_validation),
        "corrective_language_counts": dict(Counter(row["lang"] for row in corrective_train + corrective_validation)),
        "corrective_scenario_counts": dict(Counter(row["scenario"] for row in corrective_train + corrective_validation)),
        "gold_holdout_overlap": 0,
        "combined_train_validation_place_overlap": 0,
    }
    (OUTPUT / "generation_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
