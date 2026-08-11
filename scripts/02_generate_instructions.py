"""
Generates an English, voice-style instruction dataset from
data/processed/places.json for LLM fine-tuning.

For each place, produces several instruction/response pairs across scenario
types (single recommendation, comparison with a nearby alternative,
budget-constrained, safety/weather-aware, mini day-trip), grounded in the
place's real fields - especially `description`, which anchors the tone,
with facts (price, hours, safety, timing) woven in as natural sentences
rather than read out as a field list.

NOTE: Sinhala/Tamil generation is intentionally NOT included here. The
source dataset only has English `description` text - a naive template that
inserts English description text into Sinhala/Tamil sentences produces
unnatural, stitched-together output, not genuine native-quality Sinhala/
Tamil. Multilingual training data needs real Sinhala/Tamil descriptions
(human-written or carefully reviewed translations) before it can be
generated the same way this script generates English - see project plan.

Usage:
    python scripts/02_generate_instructions.py
"""

import json
import math
import random
from pathlib import Path

from travel_facts import TRAVEL_FACTS

PROCESSED_DIR = Path(__file__).resolve().parent.parent / "data" / "processed"
TRAINING_DIR = Path(__file__).resolve().parent.parent / "data" / "training"

SYSTEM_PROMPT_EN = (
    "You are TripMe, a warm and knowledgeable Sri Lankan travel voice assistant. "
    "Reply naturally in English, using only the facts provided about each place. "
    "Never invent facts, prices, hours, or details that aren't given to you - "
    "if something isn't provided, say you don't know rather than guessing."
)

# Same voice/grounding rule as SYSTEM_PROMPT_EN, plus one extra line: think
# through the request before answering, and show that thinking. Kept as its
# own short prompt (not a longer general-purpose one) so only the scenario
# that actually needs visible reasoning - trip planning, where there are
# real tradeoffs to weigh (budget, pace, interests, day count) - pays for it.
SYSTEM_PROMPT_TRIP_PLAN_EN = (
    "You are TripMe, a warm and knowledgeable Sri Lankan travel voice assistant. "
    "Reply naturally in English, using only the facts provided about each place. "
    "Never invent facts, prices, hours, or details that aren't given to you - "
    "if something isn't provided, say you don't know rather than guessing. "
    "Before giving the plan, briefly think through the request out loud - which "
    "stops fit the interests and pace, whether the total cost fits the budget, "
    "and anything about weather or safety worth weighing - then give the final "
    "plan as JSON."
)


def clean_desc(desc: str) -> str:
    return " ".join(desc.split())


def sentence(text: str) -> str:
    """Ensure text reads as a proper sentence: capitalized, ends with a period."""
    text = text.strip()
    if not text:
        return text
    text = text[0].upper() + text[1:]
    if text[-1] not in ".!?":
        text += "."
    return text


def lower_first(text: str) -> str:
    text = text.strip()
    return text[0].lower() + text[1:] if text else text


def money_en(price: int) -> str:
    return "free to enter" if price == 0 else f"about {price} rupees to enter"


BUDGET_ADJECTIVE_EN = {
    "free": "free",
    "budget": "budget-friendly",
    "moderate": "moderately priced",
    "expensive": "on the pricier side",
}


def budget_clause_en(budget_category: str, ticket_price: int) -> str:
    adjective = BUDGET_ADJECTIVE_EN.get(budget_category.lower(), budget_category.lower())
    if ticket_price == 0:
        return f"it's {adjective} to visit and free to enter"
    return f"it's {adjective} to visit ({money_en(ticket_price)})"


def opening_en(hours: str) -> str:
    hours = hours.strip()
    return "it's open all day" if hours.lower() == "24 hours" else f"it's open {lower_first(hours)}"


def monsoon_clause(note: str) -> str:
    """monsoon_note is free text in the source data (varying capitalization/
    punctuation) - normalize it into a clause that fits mid-sentence."""
    note = clean_desc(note).rstrip(".")
    return lower_first(note)


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

    rng = random.Random(42)
    examples = build_examples(places_by_district, rng)
    examples += build_multi_district_examples(places_by_province, rng)
    examples += build_trip_plan_examples(places_by_district, rng)
    rng.shuffle(examples)

    # Stratified split: hold out ~10% per district bucket so every district
    # is represented in both train and val.
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

    train_path = TRAINING_DIR / "train.jsonl"
    val_path = TRAINING_DIR / "val.jsonl"

    with open(train_path, "w", encoding="utf-8") as fh:
        for ex in train:
            fh.write(json.dumps(ex, ensure_ascii=False) + "\n")

    with open(val_path, "w", encoding="utf-8") as fh:
        for ex in val:
            fh.write(json.dumps(ex, ensure_ascii=False) + "\n")

    print(f"Generated {len(examples)} total examples (English only)")
    print(f"  train: {len(train)} -> {train_path}")
    print(f"  val:   {len(val)} -> {val_path}")

    from collections import Counter
    scenario_counts = Counter(ex["scenario"] for ex in train)
    print("\nBy scenario (train):")
    for scenario, count in scenario_counts.most_common():
        print(f"  {scenario:15s} {count}")


# ---------------------------------------------------------------------------
# Response builders
# ---------------------------------------------------------------------------

def resp_single_en(p: dict) -> str:
    return " ".join([
        f"{p['name']} is a great choice.",
        sentence(clean_desc(p["description"])),
        sentence(f"{opening_en(p['opening_hours'])}, and {budget_clause_en(p['budget_category'], p['ticket_price'])}"),
        sentence(f"the best time to visit is {p['best_time_to_visit']}"),
    ])


def resp_family_budget_en(p: dict) -> str:
    return " ".join([
        f"For a family day out, {p['name']} in {p['district_id']} is worth visiting.",
        sentence(clean_desc(p["description"])),
        sentence(f"{budget_clause_en(p['budget_category'], p['ticket_price'])}, "
                  f"and it's considered {p['safety_level'].lower()} for visitors"),
        sentence(f"you can enjoy {p['activities'].lower()} there"),
    ])


def resp_safety_en(p: dict) -> str:
    wildlife = ("there's no particular wildlife hazard to worry about"
                if p["wildlife_hazard"] == "None"
                else f"keep an eye out for {p['wildlife_hazard'].lower()}")
    return " ".join([
        sentence(f"{p['name']} is generally {p['safety_level'].lower()} to visit"),
        sentence(f"{wildlife}, and in terms of weather, {monsoon_clause(p['monsoon_note'])}"),
        sentence(f"the best time to go is {p['best_time_to_visit']}"),
    ])


IMPERATIVE_OPENERS = ("discover", "experience", "explore", "witness", "marvel", "uncover", "step into")


def first_clause(description: str, name: str, max_len: int = 140) -> str:
    """Take the description's opening up to the first sentence-ending
    punctuation at or before max_len, so excerpts never cut off mid-word.
    Strips a leading repeat of the place's own name (descriptions
    conventionally open with it, e.g. "Hatton Falls, a majestic cascade...")
    since the name is already stated separately in the sentence."""
    desc = clean_desc(description)
    if desc.lower().startswith(name.lower()):
        desc = desc[len(name):].lstrip(",; ")
    truncated = desc[:max_len]
    cut = max(truncated.rfind(", "), truncated.rfind("; "))
    if cut > 40:
        truncated = truncated[:cut]
    else:
        last_space = truncated.rfind(" ")
        if last_space > 40:
            truncated = truncated[:last_space]
    return truncated.rstrip(" .,;")


def excerpt_clause(description: str, name: str) -> str:
    """Build a clause suitable for `<Name> is known for {clause}`. Descriptions
    that open with an imperative verb (Discover/Experience/...) don't read as
    a noun phrase, so those get a generic fallback clause instead of being
    force-fit after "known for"."""
    excerpt = first_clause(description, name)
    if excerpt.split(" ", 1)[0].lower() in IMPERATIVE_OPENERS:
        return "its natural beauty and charm"
    return lower_first(excerpt)


def resp_compare_en(a: dict, b: dict) -> str:
    return " ".join([
        "There are a couple of good options nearby.",
        sentence(f"{a['name']} is known for {excerpt_clause(a['description'], a['name'])}, "
                  f"and it's {money_en(a['ticket_price'])}"),
        sentence(f"alternatively, {b['name']} is known for "
                  f"{excerpt_clause(b['description'], b['name'])}, "
                  f"and is {money_en(b['ticket_price'])}"),
        sentence(f"both are good picks depending on whether you'd prefer {a['activities'].lower()} "
                  f"or {b['activities'].lower()}"),
    ])


def resp_daytrip_en(trip_places: list) -> str:
    parts = [sentence(f"Here's a nice little day trip around {trip_places[0]['district_id']}")]
    for i, p in enumerate(trip_places, 1):
        parts.append(sentence(
            f"stop {i}: {p['name']}, known for "
            f"{excerpt_clause(p['description'], p['name'])}, "
            f"and {money_en(p['ticket_price'])}"
        ))
    parts.append("That should make for a well-rounded day out.")
    return " ".join(parts)


# ---------------------------------------------------------------------------
# Trip planner: multi-day itinerary, one paragraph per day, reusing the same
# excerpt/price phrasing as resp_daytrip_en rather than inventing a new
# voice for what is really the same "stop N: place, known for X, price Y"
# shape repeated across several days.
# ---------------------------------------------------------------------------

def resp_itinerary_en(region_label: str, day_plan: list) -> str:
    """`region_label` is either a single district name or a route label like
    "Kandy, Matale and Nuwara Eliya" for multi-district trips - each day's
    places may span more than one district, so when a day's stops aren't all
    in the same district as the previous day, that day's line names the
    district explicitly (e.g. "day 3, now in Nuwara Eliya: ...") rather than
    silently jumping location without saying so."""
    num_days = len(day_plan)
    parts = [sentence(f"Here's a {num_days}-day plan around {region_label}")]
    prev_district = None
    for day_num, day_places in enumerate(day_plan, 1):
        stop_clauses = [
            f"{p['name']} ({money_en(p['ticket_price'])})" for p in day_places
        ]
        if len(stop_clauses) == 1:
            stops_text = stop_clauses[0]
        else:
            stops_text = ", then ".join(stop_clauses)
        day_district = day_places[0]["district_id"]
        if day_district != prev_district:
            parts.append(sentence(f"day {day_num}, now in {day_district}: {stops_text}"))
        else:
            parts.append(sentence(f"day {day_num}: {stops_text}"))
        prev_district = day_district
    parts.append("That should give you a well-paced trip without rushing between places.")
    return " ".join(parts)


# ---------------------------------------------------------------------------
# Oracle chat: general Sri Lanka travel Q&A, not grounded in any specific
# place - answers come from the hand-written fact pool in travel_facts.py
# rather than places.json, since the source dataset has no visa/currency/
# tipping/season/etc. information at all.
# ---------------------------------------------------------------------------

def resp_oracle_en(fact: dict) -> str:
    return fact["en"]["answer"]


# ---------------------------------------------------------------------------
# Place-history oracle: same "oracle" scenario, but grounded in a specific
# place's `historical_significance` field (generated separately via
# generate_history_colab.ipynb from the Mahavamsa/Dipavamsa chronicles and
# Wikipedia - see that notebook's docstring). Only places where that field
# was actually populated get an example here; places without it are simply
# skipped rather than falling back to invented history, so the model never
# learns to answer a history question with a guess.
# ---------------------------------------------------------------------------

def resp_place_history_en(place: dict) -> str:
    return place["historical_significance"]


# ---------------------------------------------------------------------------
# Audio guide: purely immersive, second-person present-tense narration for
# when the user is standing at the place (button-triggered). Deliberately
# excludes practical facts (price, hours, safety) - those belong to the
# `single`/`safety`/`family_budget` scenarios. Built from `description`,
# which is already close to this register (see first_clause/excerpt_clause
# above), reframed with an immersive opening/closing rather than a factual
# recommendation frame.
# ---------------------------------------------------------------------------

AUDIO_GUIDE_OPENERS_EN = [
    "Take a moment here.",
    "Stand for a moment and take this in.",
    "Here you are.",
    "Pause here for a moment.",
]

AUDIO_GUIDE_CLOSERS_EN = [
    "Take your time here before you move on.",
    "Let yourself linger a little longer before continuing on.",
    "Stay a while longer if you'd like, before you continue your journey.",
]


DESC_IMPERATIVE_OPENERS_EN = ("discover ", "experience ", "explore ", "witness ", "marvel at ", "uncover ")


def primary_name(name: str) -> str:
    """Many place names have a comma/paren suffix (e.g. "Kiri Vehera,
    Kataragama", "Kataragama Maha Devale (inner shrine)") that the
    description text doesn't repeat - descriptions open with just the
    primary name. Used to match against description openings."""
    for sep in (",", "("):
        if sep in name:
            name = name.split(sep, 1)[0]
    return name.strip()


def narrativize_desc_en(description: str, name: str) -> str:
    """Turns the (already narrative) description into the body of the
    guide's narration. The opener sentence (see resp_audio_guide_en) already
    establishes "you're standing at {name}", so this deliberately does NOT
    repeat that framing - it just needs to read as a grammatically complete
    continuation regardless of how the description happens to start:
    with the place's own name followed by a noun phrase, e.g. "X, a
    majestic cascade..." (-> drop the name, prepend "It's" so the noun
    phrase has a subject+verb); with the name followed directly by a verb,
    e.g. "X stands as..." (-> drop the name, prepend "It"); with an
    imperative verb, e.g. "Discover..." (-> keep as-is, reads fine
    standalone); or with some other bare phrase (-> prepend "It")."""
    desc = clean_desc(description)
    lowered = desc.lower()
    short_name = primary_name(name)

    if lowered.startswith(short_name.lower()):
        rest = desc[len(short_name):].lstrip(" ")
        if rest.startswith(","):
            rest = rest.lstrip(", ")
            return sentence(f"it's {lower_first(rest)}")
        return sentence(f"it {lower_first(rest)}")

    if lowered.startswith(DESC_IMPERATIVE_OPENERS_EN):
        return sentence(desc)

    # Bare verb-phrase opening (e.g. "stands as a testament...") needs an
    # explicit subject to read as a complete sentence.
    return sentence(f"it {lower_first(desc)}")


def resp_audio_guide_en(p: dict, rng: random.Random) -> str:
    flavor_opener = rng.choice(AUDIO_GUIDE_OPENERS_EN)
    name_opener = f"You're standing at {p['name']}."
    closer = rng.choice(AUDIO_GUIDE_CLOSERS_EN)
    narration = narrativize_desc_en(p["description"], p["name"])
    return " ".join([flavor_opener, name_opener, narration, closer])


# ---------------------------------------------------------------------------
# Budget concierge: synthetic trip-spending scenarios grounded in real
# district ticket prices, so the model learns to reason over a running
# budget (total, spent-so-far by category, days remaining) and give
# specific, numeric, actionable advice - not a generic "stay on budget"
# reply. There's no real trip-spending data in the source dataset, so
# these numbers are synthesized (realistic ranges) rather than looked up;
# only the district's actual place prices anchor the money-saving tip.
# ---------------------------------------------------------------------------

BUDGET_CATEGORIES = ["transport", "food", "tickets", "stay"]

TRANSPORT_TIP_EN = (
    "using tuk-tuks or public buses instead of private taxis for your remaining stops"
)


def synthesize_budget_scenario(district: str, places: list, rng: random.Random) -> dict:
    """Builds one synthetic trip-budget scenario: a total budget, a spend
    breakdown across categories that sums to a plausible spent-so-far
    amount, and days remaining. The overspend/on-pace/underspend framing
    and the category skew are randomized so the generated advice varies
    across examples instead of always following the same shape."""
    total_days = rng.choice([3, 4, 5, 6, 7])
    days_elapsed = rng.randint(1, total_days - 1)
    days_remaining = total_days - days_elapsed

    total_budget = rng.choice([25000, 35000, 50000, 75000, 100000])

    # Expected pace if spending were perfectly even across the trip.
    expected_spent_ratio = days_elapsed / total_days
    # Randomly bias this scenario to be overspending, on pace, or underspending.
    pace_bias = rng.choice([
        rng.uniform(1.15, 1.4),   # overspending
        rng.uniform(0.9, 1.1),    # on pace
        rng.uniform(0.55, 0.8),   # underspending
    ])
    spent_ratio = min(0.97, expected_spent_ratio * pace_bias)
    spent = round(total_budget * spent_ratio, -2)  # round to nearest 100

    # Split spent amount across categories with one category randomly skewed high.
    skewed_category = rng.choice(BUDGET_CATEGORIES)
    weights = {c: rng.uniform(0.12, 0.22) for c in BUDGET_CATEGORIES}
    weights[skewed_category] = rng.uniform(0.35, 0.45)
    weight_sum = sum(weights.values())
    breakdown = {c: round(spent * (w / weight_sum), -2) for c, w in weights.items()}
    # Fix rounding drift so the breakdown sums exactly to `spent`.
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


def resp_budget_concierge_en(scenario: dict) -> str:
    pct_spent = round(scenario["spent"] / scenario["total_budget"] * 100)
    expected_pct = round(scenario["days_elapsed"] / scenario["total_days"] * 100)

    days_word = "day" if scenario["days_remaining"] == 1 else "days"

    if pct_spent > expected_pct + 10:
        pace_clause = f"you're a bit ahead of pace - {pct_spent}% of your budget spent with {scenario['days_remaining']} {days_word} left"
    elif pct_spent < expected_pct - 10:
        pace_clause = f"you're comfortably under pace - only {pct_spent}% of your budget spent with {scenario['days_remaining']} {days_word} left"
    else:
        pace_clause = f"you're at {pct_spent}% of your budget with {scenario['days_remaining']} {days_word} left, right on pace"

    skew_amount = scenario["breakdown"][scenario["skewed_category"]]
    skew_pct = round(skew_amount / scenario["spent"] * 100)

    tip = TRANSPORT_TIP_EN if scenario["skewed_category"] == "transport" else \
        "spacing out paid attractions with free ones for your remaining stops" if scenario["skewed_category"] == "tickets" else \
        "trying more local eateries instead of hotel/tourist restaurants for your remaining meals" if scenario["skewed_category"] == "food" else \
        "a guesthouse over a hotel for your remaining nights"

    savings_hint = ""
    if scenario["cheapest_nearby"] and scenario["cheapest_nearby"]["ticket_price"] == 0:
        savings_hint = f" {scenario['cheapest_nearby']['name']} nearby is free to enter if you want a no-cost stop."

    return " ".join([
        sentence(pace_clause),
        sentence(f"your {scenario['skewed_category']} spend is on the high side, "
                  f"at about {skew_pct}% of what you've spent so far in {scenario['district']}"),
        sentence(f"consider {tip} to bring that down") + savings_hint,
    ])


# ---------------------------------------------------------------------------
# Question templates
# ---------------------------------------------------------------------------

QUESTIONS_EN = {
    "single": [
        "What's worth visiting near {district}?",
        "Tell me about a good place to visit in {district}.",
        "Is there anything interesting to see around {district}?",
    ],
    "family_budget": [
        "Where's a good free place for a family day out near {district}?",
        "I'm on a budget - any good places to visit in {district}?",
        "Suggest a {budget} place near {district} for the family.",
    ],
    "safety": [
        "Is {name} safe to visit right now?",
        "What should I know about safety and weather at {name}?",
        "Any risks I should know about before visiting {name}?",
    ],
    "compare": [
        "What are some good options near {district}?",
        "Can you compare a couple of places to visit in {district}?",
    ],
    "daytrip": [
        "Can you plan a day trip around {district} for me?",
        "I have one day in {district} - what should I do?",
    ],
    "itinerary": [
        "Can you plan a {days}-day trip around {district} for me?",
        "I have {days} days in {district} - what should I do?",
        "Put together a {days}-day itinerary for {district}.",
    ],
    "itinerary_multi": [
        "Can you plan a {days}-day trip covering {region_label} for me?",
        "I have {days} days and want to visit {region_label} - what should I do?",
        "Put together a {days}-day route through {region_label}.",
    ],
    "budget_concierge": [
        "Am I overspending? Should I cut back?",
        "How's my budget looking so far?",
        "Am I on track with my spending?",
        "Where am I spending too much on this trip?",
    ],
    "audio_guide": [
        "Play the audio guide for {name}.",
        "Tell me about {name} while I'm here.",
        "Give me the audio guide for where I'm standing.",
    ],
    "place_history": [
        "What's the historical significance of {name}?",
        "Does {name} have any real history behind it?",
        "Tell me about the history of {name}.",
        "Why is {name} historically important?",
    ],
}


def budget_context_block_en(scenario: dict) -> str:
    """Formats the synthetic budget scenario as a structured context block,
    mirroring what the real app would pass in (it already has this data -
    total budget, spent-to-date by category, days elapsed/remaining). This
    is what the model conditions its numeric answer on; without it, the
    model would have to invent the percentages it reports instead of
    computing them from given data."""
    b = scenario["breakdown"]
    return (
        f"My trip: {scenario['total_days']} days in {scenario['district']}, "
        f"day {scenario['days_elapsed']} just finished ({scenario['days_remaining']} days left). "
        f"Total budget: {scenario['total_budget']} LKR. Spent so far: {scenario['spent']} LKR "
        f"(transport {b['transport']}, food {b['food']}, tickets {b['tickets']}, stay {b['stay']})."
    )


def make_example(scenario: str, question: str, answer: str, place_ids: list, district: str = None) -> dict:
    return {
        "lang": "en",
        "scenario": scenario,
        "place_ids": place_ids,
        "district": district,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT_EN},
            {"role": "user", "content": question},
            {"role": "assistant", "content": answer},
        ],
    }


def build_examples(places_by_district: dict, rng: random.Random) -> list:
    examples = []

    for district, places in places_by_district.items():
        for p in places:
            q = rng.choice(QUESTIONS_EN["single"]).format(district=district)
            examples.append(make_example("single", q, resp_single_en(p), [p["id"]]))

            q = rng.choice(QUESTIONS_EN["family_budget"]).format(
                district=district, budget=p["budget_category"].lower()
            )
            examples.append(make_example("family_budget", q, resp_family_budget_en(p), [p["id"]]))

            q = rng.choice(QUESTIONS_EN["safety"]).format(name=p["name"])
            examples.append(make_example("safety", q, resp_safety_en(p), [p["id"]]))

            q = rng.choice(QUESTIONS_EN["audio_guide"]).format(name=p["name"])
            examples.append(make_example("audio_guide", q, resp_audio_guide_en(p, rng), [p["id"]]))

        if len(places) >= 2:
            # Generate several compare/day-trip examples per district (not just
            # one) so these scenario types are represented at a similar scale
            # to the per-place scenarios above.
            num_variants = min(5, len(places))
            for _ in range(num_variants):
                a, b = rng.sample(places, 2)
                q = rng.choice(QUESTIONS_EN["compare"]).format(district=district)
                examples.append(make_example("compare", q, resp_compare_en(a, b), [a["id"], b["id"]]))

                trip_places = rng.sample(places, min(3, len(places)))
                q = rng.choice(QUESTIONS_EN["daytrip"]).format(district=district)
                examples.append(make_example(
                    "daytrip", q, resp_daytrip_en(trip_places), [x["id"] for x in trip_places]
                ))

            # Trip planner: multi-day itineraries, only for districts with
            # enough places to give each day distinct stops without repeats.
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
                    q = rng.choice(QUESTIONS_EN["itinerary"]).format(days=len(day_plan), district=district)
                    all_ids = [p["id"] for day in day_plan for p in day]
                    examples.append(make_example(
                        "itinerary", q, resp_itinerary_en(district, day_plan), all_ids, district=district
                    ))

            # Budget concierge: several synthetic spending scenarios per
            # district, each grounded via `cheapest_nearby` so the response
            # can reference a real place/price if relevant. The budget
            # numbers are passed as part of the user turn (as the real app
            # would provide them), not left implicit - the model must learn
            # to compute its answer from given data, not invent numbers.
            for _ in range(num_variants):
                scenario = synthesize_budget_scenario(district, places, rng)
                question = rng.choice(QUESTIONS_EN["budget_concierge"])
                q = f"{budget_context_block_en(scenario)}\n\n{question}"
                place_ids = [scenario["cheapest_nearby"]["id"]] if scenario["cheapest_nearby"] else []
                examples.append(make_example(
                    "budget_concierge", q, resp_budget_concierge_en(scenario), place_ids, district=district
                ))

    # Oracle chat: general travel facts, not tied to any district or place,
    # so these are generated once globally rather than per-district. Each
    # question phrasing for a fact gets its own example (answer text is the
    # same fact, not reworded per phrasing).
    for fact in TRAVEL_FACTS:
        answer = resp_oracle_en(fact)
        for question in fact["en"]["questions"]:
            examples.append(make_example("oracle", question, answer, [], district="general"))

    # Place-specific history oracle - only for places with a real, sourced
    # historical_significance field (see resp_place_history_en above).
    for district, places in places_by_district.items():
        for p in places:
            if not p.get("historical_significance"):
                continue
            q = rng.choice(QUESTIONS_EN["place_history"]).format(name=p["name"])
            examples.append(make_example(
                "oracle", q, resp_place_history_en(p), [p["id"]], district=district
            ))

    return examples


def region_label_en(districts: list) -> str:
    """'Kandy and Matale' / 'Kandy, Matale and Nuwara Eliya'."""
    if len(districts) == 1:
        return districts[0]
    if len(districts) == 2:
        return f"{districts[0]} and {districts[1]}"
    return f"{', '.join(districts[:-1])} and {districts[-1]}"


def build_multi_district_examples(places_by_province: dict, rng: random.Random, num_variants: int = 8) -> list:
    """Multi-day itineraries spanning 2-3 districts within the same province
    (e.g. Kandy -> Matale -> Nuwara Eliya, all Central province), since
    that's the only geographic-proximity signal available in this dataset
    (see 01_merge_places.py's note that lat/lng are unreliable for
    fine-grained distance filtering) - districts grouped under the same
    province are a reasonable real-world travel route, unlike e.g. Jaffna
    paired with Galle. Each day's stops all come from one district (no
    same-day cross-district hopping - that's a pacing assumption a voice
    assistant shouldn't make for the user), and consecutive days are ordered
    so the route only advances through districts, never backtracks."""
    examples = []
    for province, districts_map in places_by_province.items():
        eligible_districts = [d for d, places in districts_map.items() if len(places) >= 2]
        if len(eligible_districts) < 2:
            continue  # need at least 2 districts in this province to build a route

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

            region_label = region_label_en(route_districts)
            q = rng.choice(QUESTIONS_EN["itinerary_multi"]).format(
                days=len(day_plan), region_label=region_label
            )
            all_ids = [p["id"] for day in day_plan for p in day]
            examples.append(make_example(
                "itinerary_multi", q, resp_itinerary_en(region_label, day_plan),
                all_ids, district=province
            ))
    return examples


# ---------------------------------------------------------------------------
# Structured trip planner: JSON-in / JSON-out, for an app-side "Trip Planner"
# feature (not the voice chat scenarios above). Input is a structured request
# (budget_lkr, days, destination district, interests, pace); output is a
# structured per-day plan (day_theme, notes, human_text, safety_tip,
# sinhala_phrase, and the real stop data - id/name/lat/lng/price copied
# directly from places.json, never invented or re-estimated by the model).
# ---------------------------------------------------------------------------

# Maps a user-facing "interest" tag to the place categories that satisfy it.
# Categories not listed under any interest (e.g. "Other", "House") are simply
# never selected by this scenario - there's no interest tag vague enough to
# honestly cover them.
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

# Rough average travel speed by road_condition, used only to turn a
# haversine straight-line distance into an approximate driving time. This is
# NOT real routing (no actual road network, no traffic) - it's a cheap
# same-district estimate that's still far more honest than treating every
# pair of stops as equally far apart, which is what a plain random shuffle
# implicitly does. road_condition is read off the destination stop, since
# that's the road you're arriving on.
AVG_SPEED_KMH_BY_ROAD = {
    "Paved": 40,
    "Unpaved": 20,
    "Mixed": 30,
}
DEFAULT_AVG_SPEED_KMH = 30


def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Straight-line distance between two lat/lng points, in kilometers."""
    r = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def travel_time_minutes(distance_km: float, road_condition: str) -> int:
    speed = AVG_SPEED_KMH_BY_ROAD.get(road_condition, DEFAULT_AVG_SPEED_KMH)
    return round(distance_km / speed * 60)


def nearest_neighbor_order(places: list, start: dict) -> list:
    """Greedy nearest-neighbor ordering: starting from `start`, repeatedly
    picks whichever remaining place is closest (haversine) to the last one
    added. Not an optimal route (that's a much harder problem), but it
    turns a random stop order into a sensible "visit what's nearby next"
    order using only real coordinates, which is what actually matters for
    a same-day, same-district itinerary."""
    remaining = places[:]
    ordered = [start]
    remaining.remove(start)
    while remaining:
        last = ordered[-1]
        nxt = min(
            remaining,
            key=lambda p: haversine_km(last["lat"], last["lng"], p["lat"], p["lng"]),
        )
        ordered.append(nxt)
        remaining.remove(nxt)
    return ordered


def cluster_into_days(places: list, days: int, min_stops: int, max_stops: int,
                       rng: random.Random) -> list:
    """Splits `places` into up to `days` day-groups, each geographically
    coherent rather than an arbitrary slice. Picks a random unused place as
    the day's seed, then greedily claims its nearest unused neighbors up to
    that day's stop count - so a day's stops are the ones actually close to
    each other, not whichever ones happened to land in the same slice of a
    shuffled list."""
    remaining = places[:]
    day_groups = []
    for _ in range(days):
        if not remaining:
            break
        stops_today_count = min(rng.randint(min_stops, max_stops), len(remaining))
        if stops_today_count <= 0:
            break
        seed = rng.choice(remaining)
        remaining.remove(seed)
        group = [seed]
        for _ in range(stops_today_count - 1):
            if not remaining:
                break
            nxt = min(
                remaining,
                key=lambda p: haversine_km(seed["lat"], seed["lng"], p["lat"], p["lng"]),
            )
            group.append(nxt)
            remaining.remove(nxt)
        # Sequence this day's stops as a nearest-neighbor route starting
        # from the seed, so consecutive stops in the plan are actually
        # close to each other rather than in pick order.
        day_groups.append(nearest_neighbor_order(group, seed))
    return day_groups


def day_theme_en(categories_today: list) -> str:
    """Short label from the day's actual categories - 'Waterfalls & Nature
    Day' etc - not a generic 'Day N' placeholder."""
    cat_to_label = {
        "Cascade": "Waterfalls", "Plunge": "Waterfalls", "Tiered": "Waterfalls",
        "Fan": "Waterfalls", "Horsetail": "Waterfalls", "Block": "Waterfalls",
        "Segmented": "Waterfalls", "Multi-step": "Waterfalls",
        "National Park": "Wildlife", "Sandy Beach": "Beach", "Urban Beach": "Beach",
        "Cave": "Caves", "Forest Monastery": "Forest", "Tea Estate": "Tea Country",
        "Temple": "Temples", "Buddhist Temple": "Temples", "Kovil": "Kovils",
        "Church": "Churches", "Mosque": "Mosques", "Cathedral": "Heritage",
        "Devalaya": "Devales", "Devale": "Devales", "Stupa": "Stupas",
        "Building": "Heritage", "Ruins": "Ruins", "Pre-Historic Site": "History",
        "Ambalama": "Heritage", "Adventure Park": "Adventure",
    }
    labels = []
    for cat in categories_today:
        label = cat_to_label.get(cat, cat)
        if label not in labels:
            labels.append(label)
    if not labels:
        return "Exploring"
    if len(labels) == 1:
        return f"{labels[0]} Day"
    return f"{' & '.join(labels[:2])} Day"


def safety_tip_en(stops_today: list) -> str:
    """One safety note for the day, picked from whichever stop actually has
    something noteworthy (a real wildlife_hazard, a guide requirement, or a
    non-Safe safety_level) - grounded in that place's real fields, never a
    generic invented caution. Falls back to a plain reassurance only if none
    of the day's stops have anything to flag."""
    for p in stops_today:
        if p.get("wildlife_hazard") and p["wildlife_hazard"] != "None":
            return f"At {p['name']}, watch for {p['wildlife_hazard'].lower()}."
        if p.get("guide_required", "no").lower() == "yes":
            return f"{p['name']} requires a guide - arrange one before you go."
        if p.get("safety_level", "Safe").lower() != "safe":
            return f"{p['name']} is rated {p['safety_level'].lower()} - take extra care there."
    return "No particular safety concerns for today's stops - standard precautions apply."


def notes_en(stops_today: list) -> str:
    """Practical facts as a compact list, not prose - opening hours, price,
    activities, and (from stop 2 onward) the haversine-estimated travel leg
    from the previous stop, exactly as computed (no rounding beyond what
    travel_time_minutes already does)."""
    lines = []
    for i, p in enumerate(stops_today):
        entry = (
            f"{p['name']}: {p['opening_hours']}, {money_en(p['ticket_price'])}, "
            f"activities: {p['activities'].lower()}"
        )
        if i > 0:
            prev = stops_today[i - 1]
            dist_km = haversine_km(prev["lat"], prev["lng"], p["lat"], p["lng"])
            mins = travel_time_minutes(dist_km, p.get("road_condition", ""))
            entry += f" (~{dist_km:.1f} km / ~{mins} min from {prev['name']})"
        lines.append(entry)
    return " | ".join(lines)


def human_text_en(day_num: int, stops_today: list) -> str:
    stop_clauses = []
    for i, p in enumerate(stops_today):
        clause = f"{p['name']} ({money_en(p['ticket_price'])})"
        if i > 0:
            prev = stops_today[i - 1]
            dist_km = haversine_km(prev["lat"], prev["lng"], p["lat"], p["lng"])
            mins = travel_time_minutes(dist_km, p.get("road_condition", ""))
            clause = f"about {mins} min away, {clause}"
        stop_clauses.append(clause)
    stops_text = stop_clauses[0] if len(stop_clauses) == 1 else ", then ".join(stop_clauses)
    return sentence(f"day {day_num}: {stops_text}")


SINHALA_PHRASE_STUB = {
    "Waterfalls": "ඇල්ල නරඹන දිනයක්",
    "Wildlife": "වන ජීවීන් නරඹන දිනයක්",
    "Beach": "වෙරළ දිනයක්",
    "Caves": "ගුහා නරඹන දිනයක්",
    "Forest": "වන අභයභූමි දිනයක්",
    "Tea Country": "තේ වතු දිනයක්",
    "Temples": "පන්සල් වන්දනා දිනයක්",
    "Kovils": "කෝවිල් වන්දනා දිනයක්",
    "Churches": "පල්ලි වන්දනා දිනයක්",
    "Mosques": "පල්ලි වන්දනා දිනයක්",
    "Heritage": "උරුමය නරඹන දිනයක්",
    "Devales": "දේවාල වන්දනා දිනයක්",
    "Stupas": "ස්තූප වන්දනා දිනයක්",
    "Ruins": "නටබුන් නරඹන දිනයක්",
    "History": "ඉතිහාසය ගවේෂණය කරන දිනයක්",
    "Adventure": "වික්‍රමාන්විත දිනයක්",
    "Exploring": "ගවේෂණය කරන දිනයක්",
}


def sinhala_phrase_for_theme(theme_en: str) -> str:
    """Sinhala rendering of the day theme - not the whole day plan, just the
    short phrase (e.g. 'Waterfalls Day' -> 'ඇල්ල නරඹන දිනයක්'), matched
    against the labels used in day_theme_en. Falls back to the 'Exploring'
    stub for any combined/unrecognized theme rather than guessing a
    translation."""
    first_label = theme_en.split(" & ")[0].replace(" Day", "")
    return SINHALA_PHRASE_STUB.get(first_label, SINHALA_PHRASE_STUB["Exploring"])


def build_trip_plan(destination_district: str, budget_lkr: int, days: int,
                     interests: list, pace: str, places_by_district: dict,
                     rng: random.Random) -> dict | None:
    """Builds one structured trip plan, or None if there isn't enough
    matching inventory (not enough places in this district matching the
    requested interests) to honestly fill the requested number of days -
    returning nothing is correct here, not padding with irrelevant places."""
    district_places = places_by_district.get(destination_district, [])
    wanted_categories = set()
    for interest in interests:
        wanted_categories |= INTEREST_CATEGORIES.get(interest, set())
    matching_places = [p for p in district_places if p["category_id"] in wanted_categories]
    if len(matching_places) < 2:
        return None

    min_stops, max_stops = PACE_STOPS_PER_DAY.get(pace, (2, 3))
    day_groups = cluster_into_days(matching_places, days, min_stops, max_stops, rng)

    day_results = []
    running_cost = 0
    for day_num, stops_today in enumerate(day_groups, start=1):
        theme = day_theme_en([p["category_id"] for p in stops_today])
        day_cost = sum(p["ticket_price"] for p in stops_today)
        running_cost += day_cost

        day_results.append({
            "day": day_num,
            "day_theme": theme,
            "sinhala_phrase": sinhala_phrase_for_theme(theme),
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
            "notes": notes_en(stops_today),
            "human_text": human_text_en(day_num, stops_today),
            "safety_tip": safety_tip_en(stops_today),
        })

    if len(day_results) < 2:
        return None

    return {
        "days": day_results,
        "total_estimated_cost_lkr": running_cost,
        "within_budget": running_cost <= budget_lkr,
        # Internal only - used to narrate the reasoning trace (how big was
        # the candidate pool this plan was picked from). Popped off before
        # the plan is serialized into the assistant's JSON output.
        "_matching_pool_size": len(matching_places),
    }


def reasoning_en(request: dict, plan: dict, matching_pool_size: int) -> str:
    """Narrates the actual decision behind `plan` - grounded in the same
    numbers already computed for it (day themes, per-day cost, safety flags,
    interest/pace matches), not a generic 'let me think' filler. Every claim
    here must trace back to a real field on the plan or request; nothing is
    invented just to sound thoughtful."""
    interests_text = " and ".join(request["interests"])
    lines = [
        sentence(
            f"the traveler wants a {request['pace']}-paced {request['days']}-day trip "
            f"in {request['destination']} focused on {interests_text}"
        ),
        sentence(
            f"there are {matching_pool_size} places in {request['destination']} matching "
            f"those interests, enough to fill {len(plan['days'])} day"
            f"{'s' if len(plan['days']) != 1 else ''} without repeating a stop"
        ),
    ]

    for day in plan["days"]:
        stops = day["stops"]
        stop_names = ", ".join(s["name"] for s in stops)
        if len(stops) > 1:
            day_km = sum(
                haversine_km(stops[i - 1]["lat"], stops[i - 1]["lng"], stops[i]["lat"], stops[i]["lng"])
                for i in range(1, len(stops))
            )
            lines.append(sentence(
                f"day {day['day']} groups {stop_names} together as a {day['day_theme'].lower()}, "
                f"ordered by proximity so consecutive stops are close - about {day_km:.1f} km "
                f"of travel between them in total"
            ))
        else:
            lines.append(sentence(f"day {day['day']} groups {stop_names} together as a {day['day_theme'].lower()}"))
        if day["safety_tip"] and not day["safety_tip"].startswith("No particular safety"):
            lines.append(sentence(day["safety_tip"]))

    cost = plan["total_estimated_cost_lkr"]
    budget = request["budget_lkr"]
    if plan["within_budget"]:
        headroom = budget - cost
        if cost == 0:
            lines.append(sentence("every stop on this plan is free to enter, so it comfortably fits any budget"))
        else:
            lines.append(sentence(
                f"total cost comes to {cost} rupees against a {budget} rupee budget, "
                f"leaving {headroom} rupees of headroom, so this fits"
            ))
    else:
        over_by = cost - budget
        lines.append(sentence(
            f"total cost comes to {cost} rupees, which is {over_by} rupees over the "
            f"{budget} rupee budget - flagging that rather than quietly dropping a stop"
        ))

    return " ".join(lines)


def build_trip_plan_examples(places_by_district: dict, rng: random.Random, num_variants: int = 6) -> list:
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

            plan = build_trip_plan(district, 0, days, interests, pace, places_by_district, rng)
            if plan is None:
                continue

            # Most places in this dataset are free/cheap (see README known
            # issues), so a budget drawn independently of the actual plan
            # cost almost never comes out under it - the model would never
            # see a genuine "over budget" example. Force roughly 1 in 4
            # variants to use a budget set just below the plan's real cost
            # (or a small nominal budget if the plan costs nothing), so
            # within_budget: false is represented in training, not just
            # always-true.
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
            matching_pool_size = plan.pop("_matching_pool_size")
            reasoning = reasoning_en(request, plan, matching_pool_size)
            assistant_content = f"{reasoning}\n\n{json.dumps(plan, ensure_ascii=False)}"

            all_ids = [s["place_id"] for day in plan["days"] for s in day["stops"]]
            examples.append({
                "lang": "en",
                "scenario": "trip_plan_structured",
                "place_ids": all_ids,
                "district": district,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT_TRIP_PLAN_EN},
                    {"role": "user", "content": json.dumps(request, ensure_ascii=False)},
                    {"role": "assistant", "content": assistant_content},
                ],
            })
    return examples


if __name__ == "__main__":
    main()
