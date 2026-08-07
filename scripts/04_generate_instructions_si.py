"""
Generates a Sinhala, voice-style instruction dataset from
data/processed/places.json for fine-tuning ihalage/llama3-sinhala
(a Llama-3-8B-Instruct model already adapted for Sinhala).

Mirrors the scenario structure of 02_generate_instructions.py (single
recommendation, family/budget, safety/weather, compare, day-trip), but
every sentence is hand-written, grammatically correct, formal Sinhala -
NOT a machine translation of the English `description` field. The source
dataset has no Sinhala description text, so responses are built by
composing fixed Sinhala clauses around the place's structured facts
(name, district, category, budget, safety, timing, activities) rather
than trying to translate free-form English prose. This avoids the
stitched/unnatural output seen when raw English text was pasted into
Sinhala templates in an earlier version of this pipeline.

Usage:
    python scripts/04_generate_instructions_si.py
"""

import json
import random
from pathlib import Path

from sinhala_activities import activities_si as translate_activities_si
from sinhala_names import name_si
from travel_facts import TRAVEL_FACTS

PROCESSED_DIR = Path(__file__).resolve().parent.parent / "data" / "processed"
TRAINING_DIR = Path(__file__).resolve().parent.parent / "data" / "training"

SYSTEM_PROMPT_SI = (
    "ඔබ TripMe නම් වූ, ශ්‍රී ලංකාවේ සංචාරක ස්ථාන පිළිබඳ නිර්දේශ ලබා දෙන කථන සහායකයෙකි. "
    "ලබා දී ඇති කරුණු පමණක් භාවිතා කරමින්, පිරිසිදු හා විධිමත් සිංහල භාෂාවෙන් "
    "ස්වාභාවිකව හා උණුසුම්ව පිළිතුරු දෙන්න."
)

# ---------------------------------------------------------------------------
# Category name translations (category_id values appearing in the dataset)
# ---------------------------------------------------------------------------

CATEGORY_SI = {
    "Temple": "පන්සල", "Kovil": "කෝවිල", "Mosque": "පල්ලිය", "Church": "පල්ලිය",
    "Cathedral": "මහා දේවස්ථානය", "Devale": "දේවාලය", "Devalaya": "දේවාලය",
    "Stupa": "ස්තූපය", "Shrine": "සිද්ධස්ථානය", "Sanctuary": "අභයභූමිය",
    "Cave Temple": "ගල් විහාරය", "Forest Monastery": "අරණ්‍ය සේනාසනය",
    "Monastery": "සේනාසනය", "Chapel": "දේවස්ථානය",
    "Cascade": "දිය ඇල්ල", "Plunge": "දිය ඇල්ල", "Tiered": "පියගැට දිය ඇල්ල",
    "Fan": "දිය ඇල්ල", "Horsetail": "දිය ඇල්ල", "Block": "දිය ඇල්ල",
    "Segmented": "දිය ඇල්ල", "Multi-step": "පියගැට දිය ඇල්ල",
    "Sandy Beach": "වැලි වෙරළ", "Urban Beach": "නගර වෙරළ", "Surf Beach": "රළ නැගීමේ වෙරළ",
    "Cove Beach": "කුඩා බොක්කක් සහිත වෙරළ", "Secluded Beach": "හුදෙකලා වෙරළ",
    "Island Beach": "දූපත් වෙරළ", "Lagoon-side Beach": "කලපු අද්දර වෙරළ",
    "Tea Estate": "තේ වතුයාය",
    "Adventure Park": "වික්‍රමාන්විත උද්‍යානය",
    "National Park": "ජාතික උද්‍යානය", "Marine National Park": "සමුද්‍ර ජාතික උද්‍යානය",
}

DEFAULT_CATEGORY_SI = "ස්ථානය"

# ---------------------------------------------------------------------------
# Field-value clause builders
# ---------------------------------------------------------------------------

def category_si(category_id: str) -> str:
    return CATEGORY_SI.get(category_id, DEFAULT_CATEGORY_SI)


def money_si(price: int) -> str:
    if price == 0:
        return "ප්‍රවේශ පත්‍රයක් අවශ්‍ය නොවේ"
    return f"ප්‍රවේශ ගාස්තුව රුපියල් {price} ක් පමණ වේ"


def budget_adjective_si(budget_category: str) -> str:
    mapping = {
        "free": "නොමිලේ",
        "budget": "අඩු වියදම් සහිත",
        "moderate": "මධ්‍යම මට්ටමේ වියදමක් සහිත",
        "expensive": "තරමක් වියදම් අධික",
    }
    return mapping.get(budget_category.lower(), budget_category)


def opening_si(hours: str) -> str:
    hours = hours.strip()
    lowered = hours.lower()

    if lowered in ("24 hours", "24/7", "all day", "all year round", "open daily 24/7", "open daily 24 hours", "open 24/7"):
        return "දිවා රාත්‍රී විවෘතව පවතී"

    if lowered == "unknown":
        return "විවෘත වේලාව නිශ්චිතව සඳහන් වී නොමැත"

    # Strip an "Open daily" prefix and trailing "daily" so only the time
    # range remains before the Sinhala clause.
    cleaned = hours
    for prefix in ("Open daily ", "Open Daily "):
        if cleaned.startswith(prefix):
            cleaned = cleaned[len(prefix):]
    if cleaned.lower().endswith(" daily"):
        cleaned = cleaned[: -len(" daily")]

    return f"විවෘත වේලාව {cleaned} වේ"


def safety_clause_si(safety_level: str) -> str:
    mapping = {
        "safe": "සංචාරකයින් සඳහා සාමාන්‍යයෙන් ආරක්ෂිත ස්ථානයකි",
        "moderate": "යම් සැලකිල්ලක් සහිතව පිවිසිය යුතු ස්ථානයකි",
        "high": "විශේෂ අවධානයෙන් හා පූර්ව සූදානමකින් යුතුව පමණක් යා යුතු ස්ථානයකි",
    }
    return mapping.get(safety_level.lower(), "සංචාරකයින් සඳහා සාමාන්‍ය ආරක්ෂාවක් සහිත ස්ථානයකි")


def wildlife_clause_si(wildlife_hazard: str) -> str:
    if wildlife_hazard.strip().lower() == "none":
        return "විශේෂිත වන සත්ව අන්තරායක් වාර්තා වී නොමැත"
    return "වන සත්වයන් සම්බන්ධයෙන් විශේෂ අවධානයෙන් සිටිය යුතුය"


def rain_clause_si(rain_sensitivity: str) -> str:
    text = rain_sensitivity.strip().lower()
    if text == "safe" or text == "none":
        return "වර්ෂාව අතරතුරදීද පිවිසීමට සාමාන්‍යයෙන් ගැටලුවක් නොවේ"
    if "dangerous" in text:
        return "අධික වර්ෂාව අතරතුරදී පිවිසීම අවදානම් විය හැක"
    if "dry season" in text or "avoid" in text or "monsoon" in text:
        return "වර්ෂා සමයේදී පිවිසීමට අපහසු විය හැකි බැවින් කලින් සැලසුම් කිරීම වැදගත් වේ"
    return "කාලගුණය අනුව පිවිසීමේ පහසුව වෙනස් විය හැක"


def activities_si_fallback(activities: str) -> str:
    """Translates the dataset's English activity phrases (e.g. 'Swimming,
    Picnicking') via sinhala_activities.activities_si - a two-tier lookup
    (common exact phrases, then keyword matching) that falls back to the
    original English text for the ~5% of phrases it doesn't recognize,
    rather than guessing at an unbacked translation."""
    return translate_activities_si(activities)


# ---------------------------------------------------------------------------
# Budget concierge: synthetic trip-spending scenarios (same numeric logic as
# 02_generate_instructions.py's synthesize_budget_scenario - duplicated here
# rather than imported, since that module's filename starts with a digit and
# isn't a clean importable name. Keep the two in sync if the logic changes.)
# ---------------------------------------------------------------------------

BUDGET_CATEGORIES = ["transport", "food", "tickets", "stay"]


def synthesize_budget_scenario(district: str, places: list, rng: random.Random) -> dict:
    total_days = rng.choice([3, 4, 5, 6, 7])
    days_elapsed = rng.randint(1, total_days - 1)
    days_remaining = total_days - days_elapsed

    total_budget = rng.choice([25000, 35000, 50000, 75000, 100000])

    expected_spent_ratio = days_elapsed / total_days
    pace_bias = rng.choice([
        rng.uniform(1.15, 1.4),
        rng.uniform(0.9, 1.1),
        rng.uniform(0.55, 0.8),
    ])
    spent_ratio = min(0.97, expected_spent_ratio * pace_bias)
    spent = round(total_budget * spent_ratio, -2)

    skewed_category = rng.choice(BUDGET_CATEGORIES)
    weights = {c: rng.uniform(0.12, 0.22) for c in BUDGET_CATEGORIES}
    weights[skewed_category] = rng.uniform(0.35, 0.45)
    weight_sum = sum(weights.values())
    breakdown = {c: round(spent * (w / weight_sum), -2) for c, w in weights.items()}
    drift = spent - sum(breakdown.values())
    breakdown[skewed_category] += drift

    cheapest_nearby = min(places, key=lambda p: p["ticket_price"]) if places else None

    return {
        "district": district,
        "total_days": total_days,
        "days_elapsed": days_elapsed,
        "days_remaining": days_remaining,
        "total_budget": int(total_budget),
        "spent": int(spent),
        "breakdown": {c: int(v) for c, v in breakdown.items()},
        "skewed_category": skewed_category,
        "cheapest_nearby": cheapest_nearby,
    }


CATEGORY_LABEL_SI = {
    "transport": "ප්‍රවාහන",
    "food": "ආහාර",
    "tickets": "ප්‍රවේශ පත්‍ර",
    "stay": "නවාතැන්",
}

CATEGORY_TIP_SI = {
    "transport": "ඉතිරි දිනවලදී පුද්ගලික කුලී රථ වෙනුවට ත්‍රී රෝද රථ හෝ පොදු බස් රථ භාවිතා කිරීම",
    "tickets": "ඉතිරි ස්ථානවලදී ගාස්තු අය කරන ස්ථාන අතරින් නොමිලේ ස්ථාන ද තෝරාගැනීම",
    "food": "ඉතිරි වේලාවලදී හෝටල්/සංචාරක අවන්හල් වෙනුවට දේශීය අවන්හල් වෙත යාම",
    "stay": "ඉතිරි රාත්‍රීවලදී හෝටලයක් වෙනුවට ගෙස්ට් හවුසියක් තෝරාගැනීම",
}


def resp_budget_concierge_si(scenario: dict) -> str:
    pct_spent = round(scenario["spent"] / scenario["total_budget"] * 100)
    expected_pct = round(scenario["days_elapsed"] / scenario["total_days"] * 100)
    days_remaining = scenario["days_remaining"]

    if pct_spent > expected_pct + 10:
        pace_clause = (
            f"ඔබගේ වියදම් සැලැස්මට වඩා තරමක් ඉදිරියෙන් සිටී. "
            f"ඉතිරිව ඇති දින {days_remaining} සඳහා, දැනට අයවැයෙන් {pct_spent}% ක් වැය වී ඇත."
        )
    elif pct_spent < expected_pct - 10:
        pace_clause = (
            f"ඔබගේ වියදම් සැලැස්මට වඩා පහළින් පවතී. "
            f"ඉතිරිව ඇති දින {days_remaining} සඳහා, දැනට අයවැයෙන් {pct_spent}% ක් පමණක් වැය වී ඇත."
        )
    else:
        pace_clause = (
            f"ඔබගේ වියදම් සැලැස්මට අනුරූපව මනාව ගමන් කරයි. "
            f"ඉතිරිව ඇති දින {days_remaining} සඳහා, දැනට අයවැයෙන් {pct_spent}% ක් වැය වී ඇත."
        )

    skew_amount = scenario["breakdown"][scenario["skewed_category"]]
    skew_pct = round(skew_amount / scenario["spent"] * 100)
    category_label = CATEGORY_LABEL_SI[scenario["skewed_category"]]
    tip = CATEGORY_TIP_SI[scenario["skewed_category"]]

    breakdown_clause = (
        f"{scenario['district']} හිදී මෙතෙක් වැය කළ මුදලින් {skew_pct}% ක්ම "
        f"{category_label} සඳහා වැය වී ඇති අතර, එය තරමක් අධික ප්‍රමාණයකි."
    )

    tip_clause = f"එය අඩු කරගැනීම සඳහා {tip} සලකා බැලිය හැක."

    savings_hint = ""
    if scenario["cheapest_nearby"] and scenario["cheapest_nearby"]["ticket_price"] == 0:
        savings_hint = (
            f" ආසන්නයේ ඇති {scenario['cheapest_nearby']['name']} වෙත ප්‍රවේශය නොමිලේ වන බැවින්, "
            f"එය වියදම් රහිත නැරඹුම් ස්ථානයක් ලෙස සලකා බැලිය හැක."
        )

    return " ".join([pace_clause, breakdown_clause, tip_clause]) + savings_hint


# ---------------------------------------------------------------------------
# Response builders per scenario
# ---------------------------------------------------------------------------

def resp_single_si(p: dict) -> str:
    cat = category_si(p["category_id"])
    return (
        f"{p['district_id']} දිස්ත්‍රික්කයේ පිහිටි {name_si(p['name'])} නම් {cat} නැරඹීමට සුදුසුය. "
        f"මෙය {budget_adjective_si(p['budget_category'])} ස්ථානයකි, {money_si(p['ticket_price'])}. "
        f"{opening_si(p['opening_hours']).capitalize()}. "
        f"එහි ගොස් සුදුසුම කාලය {p['best_time_to_visit']} වේ."
    )


def resp_family_budget_si(p: dict) -> str:
    cat = category_si(p["category_id"])
    return (
        f"පවුලේ අය සමඟ එක්දින සංචාරයක් සඳහා, {p['district_id']} දිස්ත්‍රික්කයේ පිහිටි "
        f"{name_si(p['name'])} නම් {cat} නරඹන්නට යා හැක. "
        f"මෙය {budget_adjective_si(p['budget_category'])} ස්ථානයකි, {money_si(p['ticket_price'])}. "
        f"මෙය {safety_clause_si(p['safety_level'])}. "
        f"එහිදී {activities_si_fallback(p['activities'])} වැනි ක්‍රියාකාරකම්වල නිරත විය හැක."
    )


def resp_safety_si(p: dict) -> str:
    cat = category_si(p["category_id"])
    return (
        f"{name_si(p['name'])} නම් {cat} {safety_clause_si(p['safety_level'])}. "
        f"{wildlife_clause_si(p['wildlife_hazard']).capitalize()}. "
        f"කාලගුණය සම්බන්ධයෙන් සලකන විට, {rain_clause_si(p['rain_sensitivity'])}. "
        f"එහි ගොස් වඩාත් සුදුසු කාලය {p['best_time_to_visit']} වේ."
    )


def resp_compare_si(a: dict, b: dict) -> str:
    cat_a, cat_b = category_si(a["category_id"]), category_si(b["category_id"])
    name_a, name_b = name_si(a["name"]), name_si(b["name"])
    return (
        f"ආසන්නයේ හොඳ තෝරාගැනීම් දෙකක් තිබේ. "
        f"පළමුවැන්න {name_a} නම් {cat_a} වන අතර, {money_si(a['ticket_price'])}. "
        f"දෙවැන්න {name_b} නම් {cat_b} වන අතර, {money_si(b['ticket_price'])}. "
        f"ඔබට වඩාත් සුදුසු වන්නේ {name_a} හි ඇති {activities_si_fallback(a['activities'])} වැනි "
        f"ක්‍රියාකාරකම්ද, නැතහොත් {name_b} හි ඇති {activities_si_fallback(b['activities'])} වැනි "
        f"ක්‍රියාකාරකම්ද යන්න මත රඳා පවතී."
    )


def resp_daytrip_si(trip_places: list) -> str:
    district = trip_places[0]["district_id"]
    parts = [f"{district} ප්‍රදේශය වටා දිනක සංචාරයක් මෙසේ සැලසුම් කළ හැක."]
    for i, p in enumerate(trip_places, 1):
        cat = category_si(p["category_id"])
        parts.append(
            f"{i} වන ස්ථානය ලෙස {name_si(p['name'])} නම් {cat} වෙත යා හැක, {money_si(p['ticket_price'])}."
        )
    parts.append("මෙය සම්පූර්ණ දිනක සංචාරයක් සඳහා සුදුසු සැලැස්මකි.")
    return " ".join(parts)


# ---------------------------------------------------------------------------
# Trip planner: multi-day itinerary, one sentence per day, mirroring the
# English resp_itinerary_en's day-by-day structure but built from the same
# hand-written Sinhala clause style used throughout this file (name_si,
# category_si, money_si) rather than translating the English version.
# ---------------------------------------------------------------------------

def resp_itinerary_si(district: str, day_plan: list) -> str:
    num_days = len(day_plan)
    parts = [f"{district} ප්‍රදේශය වටා දින {num_days}ක සංචාරයක් මෙසේ සැලසුම් කළ හැක."]
    for day_num, day_places in enumerate(day_plan, 1):
        stop_clauses = [
            f"{name_si(p['name'])} නම් {category_si(p['category_id'])} ({money_si(p['ticket_price'])})"
            for p in day_places
        ]
        stops_text = " ඉන්පසු ".join(stop_clauses)
        parts.append(f"{day_num} වන දිනයේදී: {stops_text}.")
    parts.append("මෙය හදිසි නොවී, සුවපහසුවෙන් ගමන් කළ හැකි සමබර සැලැස්මකි.")
    return " ".join(parts)


def district_si(district_en: str) -> str:
    """Sinhala district name, falling back to the English name for any
    district not yet in DISTRICT_SI rather than raising - keeps the
    generator resilient to a new district ever appearing in the data."""
    from sinhala_names import DISTRICT_SI
    return DISTRICT_SI.get(district_en, district_en)


def region_label_si(districts: list) -> str:
    """'මහනුවර සහ මාතලේ' / 'මහනුවර, මාතලේ සහ නුවර එළිය'."""
    names = [district_si(d) for d in districts]
    if len(names) == 1:
        return names[0]
    if len(names) == 2:
        return f"{names[0]} සහ {names[1]}"
    return f"{', '.join(names[:-1])} සහ {names[-1]}"


def resp_itinerary_multi_si(region_label: str, day_plan: list) -> str:
    """Mirrors resp_itinerary_en's multi-district behaviour: each day's stops
    all come from one district, and a day's line names its district in
    Sinhala when it differs from the previous day's, so a district switch is
    never silent."""
    num_days = len(day_plan)
    parts = [f"{region_label} ආවරණය වන දින {num_days}ක සංචාරයක් මෙසේ සැලසුම් කළ හැක."]
    prev_district = None
    for day_num, day_places in enumerate(day_plan, 1):
        stop_clauses = [
            f"{name_si(p['name'])} නම් {category_si(p['category_id'])} ({money_si(p['ticket_price'])})"
            for p in day_places
        ]
        stops_text = " ඉන්පසු ".join(stop_clauses)
        day_district = day_places[0]["district_id"]
        if day_district != prev_district:
            parts.append(f"{day_num} වන දිනයේදී, {district_si(day_district)} ප්‍රදේශයේ: {stops_text}.")
        else:
            parts.append(f"{day_num} වන දිනයේදී: {stops_text}.")
        prev_district = day_district
    parts.append("මෙය හදිසි නොවී, සුවපහසුවෙන් ගමන් කළ හැකි සමබර සැලැස්මකි.")
    return " ".join(parts)


# ---------------------------------------------------------------------------
# Oracle chat: general Sri Lanka travel Q&A, not grounded in any specific
# place - answers are the hand-written Sinhala fact text from
# travel_facts.py (written directly in Sinhala, not translated from the
# English answer), consistent with this file's overall approach.
# ---------------------------------------------------------------------------

def resp_oracle_si(fact: dict) -> str:
    return fact["si"]["answer"]


# ---------------------------------------------------------------------------
# Audio guide: purely immersive, second-person narration for when the user
# is standing at the place. Unlike the English version (which reframes the
# existing narrative `description` prose), there's no Sinhala description
# text to draw from, so this composes the narration from structured facts
# only (category family, district, activities) - grouped into a handful of
# category-family openers so a temple/kovil/church, a waterfall, a beach, a
# tea estate, and an adventure park each get language that actually fits
# what kind of place they are, rather than one generic template repeated
# for everything. Deliberately excludes practical facts (price/hours).
# ---------------------------------------------------------------------------

RELIGIOUS_CATEGORIES = {"Temple", "Kovil", "Mosque", "Church", "Cathedral", "Devale", "Devalaya",
                         "Stupa", "Shrine", "Sanctuary", "Cave Temple", "Forest Monastery",
                         "Monastery", "Chapel"}
WATERFALL_CATEGORIES = {"Cascade", "Plunge", "Tiered", "Fan", "Horsetail", "Block", "Segmented", "Multi-step"}
BEACH_CATEGORIES = {"Sandy Beach", "Urban Beach", "Surf Beach", "Cove Beach", "Secluded Beach",
                     "Island Beach", "Lagoon-side Beach"}

AUDIO_GUIDE_OPENERS_SI = [
    "මොහොතක් මෙහි නවතින්න.",
    "මොහොතක් නතර වී මේ වටපිටාව අත්විඳින්න.",
    "මෙහි ටිකක් නවතී සිටින්න.",
]

AUDIO_GUIDE_CLOSERS_SI = [
    "ඉදිරියට යාමට පෙර, මෙහි ටිකක් වේලාවක් ගත කරන්න.",
    "ඔබට කැමති නම්, ගමන දිගටම කරගෙන යාමට පෙර තව ටිකක් මෙහි රැඳී සිටින්න.",
]


def audio_guide_body_si(p: dict) -> str:
    category = p["category_id"]
    district = p["district_id"]
    activities = activities_si_fallback(p["activities"])

    if category in RELIGIOUS_CATEGORIES:
        cat = category_si(category)
        return (
            f"මෙය {district} දිස්ත්‍රික්කයේ පිහිටි, බැතිමතුන් හා සංචාරකයින් රැසක් වෙත ළඟා වන {cat}ක් වේ. "
            f"මෙහි ගොඩනැගිල්ල අවට පවතින සන්සුන් වාතාවරණය හා ගෞරවනීය ඉතිහාසය, "
            f"පැමිණෙන සෑම කෙනෙකුටම විශේෂ අත්දැකීමක් ලබා දෙයි."
        )

    if category in WATERFALL_CATEGORIES:
        return (
            f"{district} දිස්ත්‍රික්කයේ කඳුකරය මැදින් ගලා එන මෙම දිය ඇල්ල, "
            f"එහි වැටෙන ජලයේ හඬ හා අවට හරිත ස්වභාවය නිසා නිහඬ, සිත් ඇදගන්නා තැනකි. "
            f"{activities} වැනි ක්‍රියාකාරකම් සඳහා බොහෝ දෙනා මෙහි එකතු වෙති."
        )

    if category in BEACH_CATEGORIES:
        return (
            f"{district} වෙරළ තීරයේ පිහිටි මෙම ස්ථානය, රැල්ලේ හඬ හා මුහුදු සුළඟ සමඟ "
            f"විවේකයක් ලබාගැනීමට සුදුසු තැනකි. {activities} වැනි ක්‍රියාකාරකම් සඳහා "
            f"මෙම වෙරළ ප්‍රදේශය ජනප්‍රියයි."
        )

    if category == "Tea Estate":
        return (
            f"{district} දිස්ත්‍රික්කයේ කඳු බෑවුම් අතර විහිදෙන මෙම තේ වතුයාය, "
            f"ශ්‍රී ලංකාවේ තේ කර්මාන්තයේ සම්ප්‍රදායික ජීවන රටාව ගැන අවබෝධයක් ලබා දෙයි. "
            f"හරිත වතු බිම් අතරින් ඇවිද යාම සිත් නිවන අත්දැකීමකි."
        )

    if category == "Adventure Park":
        return (
            f"{district} දිස්ත්‍රික්කයේ පිහිටි මෙම ස්ථානයේදී, {activities} වැනි "
            f"වික්‍රමාන්විත ක්‍රියාකාරකම්වල නිරත විය හැක. ධෛර්යවන්තයින් සඳහා "
            f"මෙය අමතක නොවන අත්දැකීමක් සපයයි."
        )

    return (
        f"{district} දිස්ත්‍රික්කයේ පිහිටි මෙම ස්ථානය, එහි ස්වභාවික සුන්දරත්වය හා "
        f"සන්සුන් වාතාවරණය නිසා සංචාරකයින් අතර ජනප්‍රියයි. {activities} වැනි "
        f"ක්‍රියාකාරකම් සඳහා මෙහි එකතු විය හැක."
    )


def resp_audio_guide_si(p: dict, rng: random.Random) -> str:
    opener = rng.choice(AUDIO_GUIDE_OPENERS_SI)
    name_line = f"ඔබ දැන් සිටින්නේ {name_si(p['name'])} අබියසය."
    body = audio_guide_body_si(p)
    closer = rng.choice(AUDIO_GUIDE_CLOSERS_SI)
    return " ".join([opener, name_line, body, closer])


# ---------------------------------------------------------------------------
# Question templates
# ---------------------------------------------------------------------------

QUESTIONS_SI = {
    "single": [
        "{district} ආසන්නයේ නැරඹීමට සුදුසු ස්ථානයක් තිබේද?",
        "{district} ප්‍රදේශයේ හොඳ සංචාරක ස්ථානයක් කියන්න.",
        "{district} අවට බැලීමට සිත්ගන්නා ස්ථානයක් තිබේද?",
    ],
    "family_budget": [
        "{district} ආසන්නයේ පවුලේ අය සමඟ යා හැකි නොමිලේ ස්ථානයක් තිබේද?",
        "මට අඩු වියදමින් {district} ප්‍රදේශයේ යා හැකි ස්ථානයක් අවශ්‍යයි.",
        "{district} ආසන්නයේ පවුලට සුදුසු ස්ථානයක් යෝජනා කරන්න.",
    ],
    "safety": [
        "{name} දැන් යාමට ආරක්ෂිතද?",
        "{name} වෙත යාමේදී ආරක්ෂාව සහ කාලගුණය ගැන දැනගත යුතු දේ මොනවාද?",
        "{name} වෙත යාමට පෙර දැනගත යුතු අවදානම් තිබේද?",
    ],
    "compare": [
        "{district} ආසන්නයේ හොඳ තෝරාගැනීම් මොනවාද?",
        "{district} ප්‍රදේශයේ ස්ථාන දෙකක් සසඳා දෙන්නද?",
    ],
    "daytrip": [
        "{district} අවට එක්දින සංචාරයක් සැලසුම් කර දෙන්නද?",
        "මට {district} හි දිනයක් තිබේ, මොනවාද කළ යුත්තේ?",
    ],
    "itinerary": [
        "{district} අවට දින {days}ක සංචාරයක් සැලසුම් කර දෙන්නද?",
        "මට {district} හි දින {days}ක් තිබේ, මොනවාද කළ යුත්තේ?",
        "{district} සඳහා දින {days}ක සංචාරක සැලැස්මක් සකසා දෙන්න.",
    ],
    "itinerary_multi": [
        "{region_label} ආවරණය වන දින {days}ක සංචාරයක් සැලසුම් කර දෙන්නද?",
        "මට දින {days}ක් තිබේ, {region_label} බැලීමට කැමතියි - මොනවාද කළ යුත්තේ?",
        "{region_label} හරහා දින {days}ක ගමන් මාර්ගයක් සකසා දෙන්න.",
    ],
    "budget_concierge": [
        "මම වැඩිපුර වියදම් කරනවාද? මම අඩු කරගත යුතුද?",
        "මගේ අයවැය දැනට කොහොමද තිබෙන්නේ?",
        "මම මගේ වියදම් සැලැස්මට අනුව ගමන් කරනවාද?",
        "මම වැඩිපුර වියදම් කරන්නේ කොහෙද?",
    ],
    "audio_guide": [
        "{name} ගැන කථන මාර්ගෝපදේශය අරඹන්න.",
        "මම මෙහි ඉන්නකොට {name} ගැන කියන්න.",
        "මම දැන් ඉන්න තැන ගැන කථන මාර්ගෝපදේශය දෙන්න.",
    ],
}


def budget_context_block_si(scenario: dict) -> str:
    """Formats the synthetic budget scenario as a structured context block
    the model conditions its numeric answer on - mirrors what the real app
    would pass in, so the model computes from given data instead of
    inventing the percentages/amounts it reports."""
    b = scenario["breakdown"]
    return (
        f"මගේ සංචාරය: {scenario['district']} හි දින {scenario['total_days']}ක්, "
        f"දින {scenario['days_elapsed']}ක් අවසන් වී ඇත (ඉතිරිව ඇත්තේ දින {scenario['days_remaining']}ක්). "
        f"මුළු අයවැය: රුපියල් {scenario['total_budget']}. මෙතෙක් වැය කළ මුදල: රුපියල් {scenario['spent']} "
        f"(ප්‍රවාහන {b['transport']}, ආහාර {b['food']}, ප්‍රවේශ පත්‍ර {b['tickets']}, නවාතැන් {b['stay']})."
    )


def make_example(scenario: str, question: str, answer: str, place_ids: list, district: str = None) -> dict:
    return {
        "lang": "si",
        "scenario": scenario,
        "place_ids": place_ids,
        "district": district,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT_SI},
            {"role": "user", "content": question},
            {"role": "assistant", "content": answer},
        ],
    }


def build_examples(places_by_district: dict, rng: random.Random) -> list:
    examples = []

    for district, places in places_by_district.items():
        for p in places:
            q = rng.choice(QUESTIONS_SI["single"]).format(district=district)
            examples.append(make_example("single", q, resp_single_si(p), [p["id"]]))

            q = rng.choice(QUESTIONS_SI["family_budget"]).format(district=district)
            examples.append(make_example("family_budget", q, resp_family_budget_si(p), [p["id"]]))

            q = rng.choice(QUESTIONS_SI["safety"]).format(name=p["name"])
            examples.append(make_example("safety", q, resp_safety_si(p), [p["id"]]))

            q = rng.choice(QUESTIONS_SI["audio_guide"]).format(name=p["name"])
            examples.append(make_example("audio_guide", q, resp_audio_guide_si(p, rng), [p["id"]]))

        if len(places) >= 2:
            num_variants = min(5, len(places))
            for _ in range(num_variants):
                a, b = rng.sample(places, 2)
                q = rng.choice(QUESTIONS_SI["compare"]).format(district=district)
                examples.append(make_example("compare", q, resp_compare_si(a, b), [a["id"], b["id"]]))

                trip_places = rng.sample(places, min(3, len(places)))
                q = rng.choice(QUESTIONS_SI["daytrip"]).format(district=district)
                examples.append(make_example(
                    "daytrip", q, resp_daytrip_si(trip_places), [x["id"] for x in trip_places]
                ))

            if len(places) >= 4:
                for _ in range(num_variants):
                    max_days = min(5, len(places) // 2)
                    num_days = rng.randint(2, max(2, max_days))
                    shuffled = places[:]
                    rng.shuffle(shuffled)
                    day_plan, cursor = [], 0
                    for _ in range(num_days):
                        stops_today = min(rng.choice([2, 3]), len(shuffled) - cursor)
                        if stops_today <= 0:
                            break
                        day_plan.append(shuffled[cursor:cursor + stops_today])
                        cursor += stops_today
                    if len(day_plan) < 2:
                        continue
                    q = rng.choice(QUESTIONS_SI["itinerary"]).format(days=len(day_plan), district=district)
                    all_ids = [p["id"] for day in day_plan for p in day]
                    examples.append(make_example(
                        "itinerary", q, resp_itinerary_si(district, day_plan), all_ids, district=district
                    ))

            for _ in range(num_variants):
                scenario = synthesize_budget_scenario(district, places, rng)
                question = rng.choice(QUESTIONS_SI["budget_concierge"])
                q = f"{budget_context_block_si(scenario)}\n\n{question}"
                place_ids = [scenario["cheapest_nearby"]["id"]] if scenario["cheapest_nearby"] else []
                examples.append(make_example(
                    "budget_concierge", q, resp_budget_concierge_si(scenario), place_ids, district=district
                ))

    for fact in TRAVEL_FACTS:
        answer = resp_oracle_si(fact)
        for question in fact["si"]["questions"]:
            examples.append(make_example("oracle", question, answer, [], district="general"))

    return examples


def build_multi_district_examples_si(places_by_province: dict, rng: random.Random, num_variants: int = 8) -> list:
    """Sinhala counterpart of 02_generate_instructions.py's
    build_multi_district_examples - same province-grouping/route-ordering
    logic (see that function's docstring), producing hand-composed Sinhala
    output via resp_itinerary_multi_si instead of a translation."""
    examples = []
    for province, districts_map in places_by_province.items():
        eligible_districts = [d for d, places in districts_map.items() if len(places) >= 2]
        if len(eligible_districts) < 2:
            continue

        for _ in range(num_variants):
            num_districts_in_route = rng.randint(2, min(3, len(eligible_districts)))
            route_districts = rng.sample(eligible_districts, num_districts_in_route)

            day_plan = []
            for district in route_districts:
                district_places = districts_map[district]
                num_days_here = rng.randint(1, 2) if len(district_places) >= 4 else 1
                shuffled = district_places[:]
                rng.shuffle(shuffled)
                cursor = 0
                for _ in range(num_days_here):
                    stops_today = min(rng.choice([2, 3]), len(shuffled) - cursor)
                    if stops_today <= 0:
                        break
                    day_plan.append(shuffled[cursor:cursor + stops_today])
                    cursor += stops_today

            if len(day_plan) < 2:
                continue

            region_label = region_label_si(route_districts)
            q = rng.choice(QUESTIONS_SI["itinerary_multi"]).format(
                days=len(day_plan), region_label=region_label
            )
            all_ids = [p["id"] for day in day_plan for p in day]
            examples.append(make_example(
                "itinerary_multi", q, resp_itinerary_multi_si(region_label, day_plan),
                all_ids, district=province
            ))
    return examples


# ---------------------------------------------------------------------------
# Structured trip planner (Sinhala): same INTEREST_CATEGORIES/PACE_STOPS_PER_DAY
# selection and budget logic as 02_generate_instructions.py's English version
# (kept identical so both languages produce the same plan given the same
# random seed's draws) - only notes/human_text/safety_tip/day_theme text
# generation is Sinhala-specific here, hand-composed, not translated.
# ---------------------------------------------------------------------------

INTEREST_CATEGORIES = {
    "nature": {
        "Cascade", "Plunge", "Tiered", "Fan", "Horsetail", "Block", "Segmented",
        "Multi-step", "National Park", "Sandy Beach", "Urban Beach", "Cave",
        "Forest Monastery", "Tea Estate",
    },
    "culture": {
        "Temple", "Buddhist Temple", "Kovil", "Church", "Mosque", "Cathedral",
        "Devalaya", "Devale", "Stupa", "Building", "Ruins", "Pre-Historic Site",
        "Ambalama",
    },
    "adventure": {"Adventure Park", "National Park", "Cave"},
    "relaxation": {"Tea Estate", "Sandy Beach", "Urban Beach"},
}

PACE_STOPS_PER_DAY = {
    "relaxed": (1, 2),
    "moderate": (2, 3),
    "packed": (3, 4),
}

DAY_THEME_LABEL_SI = {
    "Cascade": "ඇල්ල", "Plunge": "ඇල්ල", "Tiered": "ඇල්ල", "Fan": "ඇල්ල",
    "Horsetail": "ඇල්ල", "Block": "ඇල්ල", "Segmented": "ඇල්ල", "Multi-step": "ඇල්ල",
    "National Park": "වන ජීවී", "Sandy Beach": "වෙරළ", "Urban Beach": "වෙරළ",
    "Cave": "ගුහා", "Forest Monastery": "වන අභයභූමි", "Tea Estate": "තේ වතු",
    "Temple": "පන්සල්", "Buddhist Temple": "පන්සල්", "Kovil": "කෝවිල්",
    "Church": "පල්ලි", "Mosque": "පල්ලි", "Cathedral": "උරුමය",
    "Devalaya": "දේවාල", "Devale": "දේවාල", "Stupa": "ස්තූප",
    "Building": "උරුමය", "Ruins": "නටබුන්", "Pre-Historic Site": "ඉතිහාස",
    "Ambalama": "උරුමය", "Adventure Park": "වික්‍රමාන්විත",
}


def day_theme_si(categories_today: list) -> str:
    labels = []
    for cat in categories_today:
        label = DAY_THEME_LABEL_SI.get(cat, "ගවේෂණ")
        if label not in labels:
            labels.append(label)
    if not labels:
        return "ගවේෂණය කරන දිනයක්"
    if len(labels) == 1:
        return f"{labels[0]} වන්දනා දිනයක්" if labels[0] in (
            "පන්සල්", "කෝවිල්", "පල්ලි", "දේවාල", "ස්තූප"
        ) else f"{labels[0]} නරඹන දිනයක්"
    return f"{labels[0]} සහ {labels[1]} නරඹන දිනයක්"


def safety_tip_si(stops_today: list) -> str:
    for p in stops_today:
        if p.get("wildlife_hazard") and p["wildlife_hazard"] != "None":
            return f"{name_si(p['name'])} අසල {p['wildlife_hazard'].lower()} ගැන සැලකිලිමත් වන්න."
        if p.get("guide_required", "no").lower() == "yes":
            return f"{name_si(p['name'])} සඳහා මාර්ගෝපදේශකයෙකු අවශ්‍ය වේ - කලින් සූදානම් කරගන්න."
        if p.get("safety_level", "Safe").lower() != "safe":
            return f"{name_si(p['name'])} {p['safety_level'].lower()} මට්ටමේ ස්ථානයකි - වැඩි සැලකිල්ලක් දක්වන්න."
    return "අද දින ස්ථාන සඳහා විශේෂ ආරක්ෂක අවදානම් නොමැත - සාමාන්‍ය පරිස්සම ප්‍රමාණවත් වේ."


def notes_si(stops_today: list) -> str:
    lines = []
    for p in stops_today:
        lines.append(
            f"{name_si(p['name'])}: {p['opening_hours']}, {money_si(p['ticket_price'])}, "
            f"ක්‍රියාකාරකම්: {activities_si_fallback(p['activities'])}"
        )
    return " | ".join(lines)


def human_text_si_trip(day_num: int, stops_today: list) -> str:
    stop_clauses = [
        f"{name_si(p['name'])} නම් {category_si(p['category_id'])} ({money_si(p['ticket_price'])})"
        for p in stops_today
    ]
    stops_text = " ඉන්පසු ".join(stop_clauses)
    return f"{day_num} වන දිනයේදී: {stops_text}."


def sinhala_phrase_for_theme_si(theme_si: str) -> str:
    """The structured output's dedicated sinhala_phrase field mirrors the
    English version's day_theme, but since this whole pipeline already
    generates day_theme in Sinhala, that IS the natural-language phrase -
    no separate stub table needed here (unlike the English generator, which
    needs SINHALA_PHRASE_STUB to render a Sinhala phrase from an English
    theme label)."""
    return theme_si


def build_trip_plan_si(destination_district: str, budget_lkr: int, days: int,
                        interests: list, pace: str, places_by_district: dict,
                        rng: random.Random) -> dict | None:
    district_places = places_by_district.get(destination_district, [])
    wanted_categories = set()
    for interest in interests:
        wanted_categories |= INTEREST_CATEGORIES.get(interest, set())
    matching_places = [p for p in district_places if p["category_id"] in wanted_categories]
    if len(matching_places) < 2:
        return None

    shuffled = matching_places[:]
    rng.shuffle(shuffled)
    min_stops, max_stops = PACE_STOPS_PER_DAY.get(pace, (2, 3))

    day_results = []
    cursor = 0
    running_cost = 0
    for day_num in range(1, days + 1):
        stops_today_count = min(rng.randint(min_stops, max_stops), len(shuffled) - cursor)
        if stops_today_count <= 0:
            break
        stops_today = shuffled[cursor:cursor + stops_today_count]
        cursor += stops_today_count

        theme = day_theme_si([p["category_id"] for p in stops_today])
        day_cost = sum(p["ticket_price"] for p in stops_today)
        running_cost += day_cost

        day_results.append({
            "day": day_num,
            "day_theme": theme,
            "sinhala_phrase": sinhala_phrase_for_theme_si(theme),
            "stops": [
                {
                    "place_id": p["id"],
                    "name": p["name"],
                    "lat": p["lat"],
                    "lng": p["lng"],
                    "price": p["ticket_price"],
                    "category": p["category_id"],
                }
                for p in stops_today
            ],
            "notes": notes_si(stops_today),
            "human_text": human_text_si_trip(day_num, stops_today),
            "safety_tip": safety_tip_si(stops_today),
        })

    if len(day_results) < 2:
        return None

    return {
        "days": day_results,
        "total_estimated_cost_lkr": running_cost,
        "within_budget": running_cost <= budget_lkr,
    }


def build_trip_plan_examples_si(places_by_district: dict, rng: random.Random, num_variants: int = 6) -> list:
    examples = []
    interest_combos = [
        ["nature"], ["culture"], ["nature", "culture"],
        ["adventure"], ["relaxation"], ["culture", "relaxation"],
    ]
    paces = ["relaxed", "moderate", "packed"]

    for district in places_by_district:
        for variant_i in range(num_variants):
            interests = rng.choice(interest_combos)
            pace = rng.choice(paces)
            days = rng.randint(2, 4)

            plan = build_trip_plan_si(district, 0, days, interests, pace, places_by_district, rng)
            if plan is None:
                continue

            actual_cost = plan["total_estimated_cost_lkr"]
            if variant_i % 4 == 0:
                budget_lkr = max(100, actual_cost - rng.randint(200, 1000)) if actual_cost > 0 else rng.choice([300, 500])
            else:
                budget_lkr = rng.choice([5000, 10000, 15000, 25000, 40000])
            plan["within_budget"] = actual_cost <= budget_lkr

            request = {
                "budget_lkr": budget_lkr,
                "days": days,
                "destination": district,
                "interests": interests,
                "pace": pace,
            }
            all_ids = [s["place_id"] for day in plan["days"] for s in day["stops"]]
            examples.append({
                "lang": "si",
                "scenario": "trip_plan_structured",
                "place_ids": all_ids,
                "district": district,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT_SI},
                    {"role": "user", "content": json.dumps(request, ensure_ascii=False)},
                    {"role": "assistant", "content": json.dumps(plan, ensure_ascii=False)},
                ],
            })
    return examples


def main() -> None:
    TRAINING_DIR.mkdir(parents=True, exist_ok=True)

    with open(PROCESSED_DIR / "places.json", encoding="utf-8") as fh:
        places = json.load(fh)

    places_by_district: dict = {}
    for p in places:
        places_by_district.setdefault(p["district_id"], []).append(p)

    places_by_province: dict = {}
    for p in places:
        places_by_province.setdefault(p["province_id"], {}).setdefault(p["district_id"], []).append(p)

    rng = random.Random(43)
    examples = build_examples(places_by_district, rng)
    examples += build_multi_district_examples_si(places_by_province, rng)
    examples += build_trip_plan_examples_si(places_by_district, rng)
    rng.shuffle(examples)

    buckets: dict = {}
    place_by_id = {p["id"]: p for p in places}
    for ex in examples:
        district = ex.get("district") or place_by_id[ex["place_ids"][0]]["district_id"]
        buckets.setdefault(district, []).append(ex)

    train, val = [], []
    for district, items in buckets.items():
        rng.shuffle(items)
        split_at = max(1, int(len(items) * 0.9)) if len(items) > 1 else len(items)
        train.extend(items[:split_at])
        val.extend(items[split_at:])

    rng.shuffle(train)
    rng.shuffle(val)

    train_path = TRAINING_DIR / "train_si.jsonl"
    val_path = TRAINING_DIR / "val_si.jsonl"

    with open(train_path, "w", encoding="utf-8") as fh:
        for ex in train:
            fh.write(json.dumps(ex, ensure_ascii=False) + "\n")

    with open(val_path, "w", encoding="utf-8") as fh:
        for ex in val:
            fh.write(json.dumps(ex, ensure_ascii=False) + "\n")

    print(f"Generated {len(examples)} total Sinhala examples")
    print(f"  train: {len(train)} -> {train_path}")
    print(f"  val:   {len(val)} -> {val_path}")

    from collections import Counter
    print("\nBy scenario (train):")
    for scenario, count in Counter(ex["scenario"] for ex in train).most_common():
        print(f"  {scenario:15s} {count}")


if __name__ == "__main__":
    main()
