"""
Partial English-to-Sinhala localization for place names in
data/processed/places.json.

Scope (deliberately limited - see project decisions in README):
- District names: hand-written, 100% accurate (only 25 of them).
- Common recurring Sinhala/Pali words (Viharaya, Ella, Devale, etc.): a
  hand-written dictionary, not algorithmic phonetic transliteration -
  automated phonetic rules for a low-resource language like Sinhala have a
  real error rate, so this only translates words we can state correctly.
- English-origin words (Falls, Beach, Park, Church, St., Centre, Safari,
  etc.) and Tamil-origin words (Kovil, Amman, Swami, Vinayagar, etc.) are
  deliberately left as-is - guessing a Sinhala transliteration for them
  would likely be wrong, and leaving them in English/Tamil is linguistically
  correct anyway (these ARE English or Tamil names, not Sinhala ones).
- Any word not in the dictionary (the long tail of place-specific words
  like "Kirindiwela", "Beruwala") is left as English - untranslated,
  not mistranslated. This is a known, intentional coverage gap.

Output format: "<Sinhala words + untranslated words> (<original English name>)"
so the full original name is always recoverable/confirmable, per project
decision to show both forms.
"""

import re

DISTRICT_SI = {
    "Ampara": "අම්පාර",
    "Anuradhapura": "අනුරාධපුරය",
    "Badulla": "බදුල්ල",
    "Batticaloa": "මඩකලපුව",
    "Colombo": "කොළඹ",
    "Galle": "ගාල්ල",
    "Gampaha": "ගම්පහ",
    "Hambantota": "හම්බන්තොට",
    "Jaffna": "යාපනය",
    "Kalutara": "කළුතර",
    "Kandy": "මහනුවර",
    "Kegalle": "කෑගල්ල",
    "Kilinochchi": "කිලිනොච්චිය",
    "Kurunegala": "කුරුණෑගල",
    "Mannar": "මන්නාරම",
    "Matale": "මාතලේ",
    "Matara": "මාතර",
    "Monaragala": "මොණරාගල",
    "Mullaitivu": "මුලතිව්",
    "Nuwara Eliya": "නුවර එළිය",
    "Polonnaruwa": "පොළොන්නරුව",
    "Puttalam": "පුත්තලම",
    "Ratnapura": "රත්නපුර",
    "Trincomalee": "ත්‍රිකුණාමලය",
    "Vavuniya": "වවුනියාව",
}

# Common Sinhala/Pali words recurring across many place names. Hand-written,
# not phonetically generated - only words we're confident are correct.
# Case-insensitive whole-word match. Deliberately excludes ambiguous English
# homographs (e.g. "Rock" as in "Rock Climb" is an English activity word
# here, not the Sinhala "gala"/rock-place-name sense) and words that only
# make sense translated in a Sinhala-Buddhist context (see "sri" below,
# handled separately since it's also common in Tamil/Hindu names).
COMMON_WORD_SI = {
    "viharaya": "විහාරය",
    "vihara": "විහාරය",
    "rajamaha": "රාජමහා",
    "raja": "රාජ",
    "maha": "මහා",
    "devale": "දේවාලය",
    "devalaya": "දේවාලය",
    "ella": "ඇල්ල",
    "oya": "ඔය",
    "gama": "ගම",
    "kanda": "කන්ද",
    "wewa": "වැව",
    "kele": "කැලේ",
    "pitiya": "පිටිය",
    "gala": "ගල",
    "thota": "තොට",
    "aramaya": "අරාමය",
    "senasanaya": "සේනාසනය",
    "pansala": "පන්සල",
    "purana": "පුරාණ",
    "bodhi": "බෝධි",
}

# "Sri" (ශ්‍රී) is a Sanskrit-derived honorific used in both Sinhala and
# Tamil/Hindu naming conventions - translate it only when the name doesn't
# also contain a Tamil/Hindu marker word, so Tamil-origin names (which we
# deliberately leave untouched, per project decision) don't get a stray
# Sinhala word inserted into them.
TAMIL_HINDU_MARKERS = {
    "kovil", "amman", "sivan", "swami", "vinayagar", "pillayar",
    "muthumari", "muththumari", "kathiresan", "vishnu",
}

# Words that must NOT be translated even though they might coincidentally
# resemble a dictionary entry, or that are unambiguously English/Tamil-origin
# business/descriptive terms appearing inside place names - listed here for
# clarity/documentation even though the default (not-in-dictionary -> keep
# English) already handles them correctly.
KNOWN_ENGLISH_OR_TAMIL_WORDS = {
    "falls", "beach", "st", "st.", "church", "mosque", "park", "national",
    "town", "grand", "tea", "garden", "estate", "stream", "trail", "walk",
    "kovil", "amman", "sivan", "jumma", "muthumari", "muththumari",
    "vinayagar", "swami", "centre", "safari", "river", "second", "area",
    "cathedral", "forest", "island", "lagoon", "fort", "farm", "herb",
    "spice", "trek", "point", "rc", "anglican", "devon",
}

WORD_SPLIT_RE = re.compile(r"([A-Za-z']+)")


def name_si(name: str) -> str:
    """Returns the name with recognized Sinhala words translated in place
    (district-name substrings and common dictionary words), leaving
    everything else (English/Tamil words, unmatched unique words) as-is.
    Appends the original English name in parentheses if any translation
    happened, per project decision to always show both forms."""
    translated_any = False
    is_tamil_hindu_name = any(
        re.search(rf"\b{re.escape(marker)}\b", name, re.I) for marker in TAMIL_HINDU_MARKERS
    )

    def replace_word(match: re.Match) -> str:
        nonlocal translated_any
        word = match.group(1)
        key = word.lower()
        if key == "sri":
            if is_tamil_hindu_name:
                return word
            translated_any = True
            return "ශ්‍රී"
        if key in COMMON_WORD_SI:
            translated_any = True
            return COMMON_WORD_SI[key]
        return word

    result = WORD_SPLIT_RE.sub(replace_word, name)

    for district_en, district_si in DISTRICT_SI.items():
        if district_en in result:
            result = result.replace(district_en, district_si)
            translated_any = True

    if not translated_any:
        return name

    # `result` already carries through any parenthetical suffix the name
    # itself has (e.g. "Jaffna Town Mosque (Second Mosque)" -> "යාපනය Town
    # Mosque (Second Mosque)"), since word substitution only touches word
    # characters. Appending "(name)" again would duplicate that suffix -
    # append the reference form using a dash instead when this happens.
    if "(" in name:
        return f"{result} - {name}"
    return f"{result} ({name})"
