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
import random
from pathlib import Path

from travel_facts import TRAVEL_FACTS

PROCESSED_DIR = Path(__file__).resolve().parent.parent / "data" / "processed"
TRAINING_DIR = Path(__file__).resolve().parent.parent / "data" / "training"

SYSTEM_PROMPT_EN = (
    "You are TripMe, a warm and knowledgeable Sri Lankan travel voice assistant. "
    "Reply naturally in English, using only the facts provided about each place."
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

    rng = random.Random(42)
    examples = build_examples(places_by_district, rng)
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

def resp_itinerary_en(district: str, day_plan: list) -> str:
    num_days = len(day_plan)
    parts = [sentence(f"Here's a {num_days}-day plan around {district}")]
    for day_num, day_places in enumerate(day_plan, 1):
        stop_clauses = [
            f"{p['name']} ({money_en(p['ticket_price'])})" for p in day_places
        ]
        if len(stop_clauses) == 1:
            stops_text = stop_clauses[0]
        else:
            stops_text = ", then ".join(stop_clauses)
        parts.append(sentence(f"day {day_num}: {stops_text}"))
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

    return examples


if __name__ == "__main__":
    main()
