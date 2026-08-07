"""
English-to-Sinhala translation for the `activities` field values in
data/processed/places.json.

The field is free text, not a fixed vocabulary (597 unique phrases across
1289 places, ranging from short terms like "Swimming" to full sentences
like "Explore the church's interior and learn about its history"). A
complete manual dictionary isn't practical or maintainable, so this uses a
two-tier approach:

1. Exact-phrase lookup for the ~50 most common phrases (covers the large
   majority of occurrences by frequency - see ACTIVITY_PHRASES_SI).
2. Keyword-based partial matching for common recurring concepts (prayer,
   photography, hiking, temple exploration, tea, etc.) that catches many
   of the longer/rarer phrase variants sharing those words.
3. Falls back to the original English text for anything unmatched, rather
   than guessing at a translation not grounded in an actual rule - an
   English word appearing in an otherwise-Sinhala sentence is a known,
   accepted tradeoff (see README), not silently wrong output.
"""

import re

ACTIVITY_PHRASES_SI = {
    "photography": "ඡායාරූප ගැනීම",
    "reflection": "නිශ්ශබ්ද භාවනාව",
    "swimming": "පිහිනීම",
    "prayer and meditation": "ප්‍රාර්ථනා කිරීම හා භාවනාව",
    "nature walk": "ස්වභාවික ඇවිදීම",
    "nature walks": "ස්වභාවික ඇවිදීම",
    "hiking": "කඳු නැගීම",
    "picnicking": "පික්නික් කිරීම",
    "picnic": "පික්නික් කිරීම",
    "relaxation": "විවේක ගැනීම",
    "sunbathing": "අව්වේ රස විඳීම",
    "snorkeling": "ස්නෝකලින් කිරීම",
    "tea plantation tour": "තේ වතුයාය සංචාරය",
    "bird watching": "පක්ෂීන් නැරඹීම",
    "historical tours": "ඓතිහාසික සංචාර",
    "history tour": "ඓතිහාසික සංචාරය",
    "meditation": "භාවනාව",
    "cultural tours": "සංස්කෘතික සංචාර",
    "pray and meditate": "ප්‍රාර්ථනා කර භාවනා කිරීම",
    "prayer and reflection": "ප්‍රාර්ථනාව හා නිශ්ශබ්ද භාවනාව",
    "take photos": "ඡායාරූප ගැනීම",
    "nature photography": "ස්වභාවික ඡායාරූප ගැනීම",
    "sightseeing": "දර්ශනීය ස්ථාන නැරඹීම",
    "cultural show": "සංස්කෘතික දර්ශනය",
    "surfing": "රළ නැගීම",
    "kayaking": "කයාකින් කිරීම",
    "scuba diving": "ගැඹුරු කිමිදීම",
    "guided tours": "මාර්ගෝපදේශක සංචාර",
    "tea tasting": "තේ රස විඳීම",
    "cycling": "බයිසිකල් පැදීම",
    "rafting": "රැෆ්ටින් කිරීම",
    "fishing": "මසුන් ඇල්ලීම",
    "elephant watching": "අලි නැරඹීම",
    "wildlife watching": "වන සතුන් නැරඹීම",
    "prayer": "ප්‍රාර්ථනාව",
    "praying": "ප්‍රාර්ථනා කිරීම",
    "ziplining": "සිප්ලයින් කිරීම",
    "zip-lining": "සිප්ලයින් කිරීම",
    "zip line tour": "සිප්ලයින් සංචාරය",
    "camping": "කඳවුරු බැඳීම",
    "jeep safari": "ජීප් සෆාරි",
    "jeep safaris": "ජීප් සෆාරි",
    "whale watching": "තල්මසුන් නැරඹීම",
    "turtle watching": "කැස්බෑවන් නැරඹීම",
    "paragliding": "පැරාග්ලයිඩින් කිරීම",
    "bungee jumping": "බන්ජි පැනීම",
    "boat ride": "බෝට්ටු සවාරිය",
    "sunset watching": "හිරු බැස යාම නැරඹීම",
}

# Keyword -> Sinhala fallback, checked when no exact phrase match is found.
# Ordered roughly by specificity (checked in this order, first match wins).
KEYWORD_PHRASES_SI = [
    (re.compile(r"\bprayer|\bpray\b|\bpraying\b|\bworship", re.I), "ප්‍රාර්ථනා කිරීම"),
    (re.compile(r"\bmeditat", re.I), "භාවනාව"),
    (re.compile(r"\bphotograph", re.I), "ඡායාරූප ගැනීම"),
    (re.compile(r"\btea\b.*\btast", re.I), "තේ රස විඳීම"),
    (re.compile(r"\btea\b", re.I), "තේ වතුයාය නැරඹීම"),
    (re.compile(r"\bhik", re.I), "කඳු නැගීම"),
    (re.compile(r"\bswim", re.I), "පිහිනීම"),
    (re.compile(r"\bbird", re.I), "පක්ෂීන් නැරඹීම"),
    (re.compile(r"\belephant", re.I), "අලි නැරඹීම"),
    (re.compile(r"\bwildlife", re.I), "වන සතුන් නැරඹීම"),
    (re.compile(r"\bhistor", re.I), "ඓතිහාසික තොරතුරු ගැන ඉගෙනගැනීම"),
    (re.compile(r"\bcarv|\bstatue|\bmural|\bruins?\b|\barchitectur", re.I), "පෞරාණික නිර්මාණ නැරඹීම"),
    (re.compile(r"\bpicnic", re.I), "පික්නික් කිරීම"),
    (re.compile(r"\bbuddh|\bhindu|\bbuddhis[tm]", re.I), "ආගමික සම්ප්‍රදායන් ගැන ඉගෙනගැනීම"),
    (re.compile(r"\bmass\b|\bsunday service|\bchristian", re.I), "ආගමික උත්සවවලට සහභාගී වීම"),
    (re.compile(r"\btemple|\bchurch|\bmosque|\bkovil|\bshrine|\bcathedral|\bmonastery|\bstupa", re.I), "පූජනීය ස්ථානය නැරඹීම"),
    (re.compile(r"\bcultur", re.I), "සංස්කෘතික අත්දැකීම"),
    (re.compile(r"\bview|\bscenic|\bsight", re.I), "දර්ශනීය දසුන් නැරඹීම"),
    (re.compile(r"\bgarden", re.I), "උයන් නැරඹීම"),
    (re.compile(r"\brelax|\btranquil|\bstroll", re.I), "විවේක ගැනීම"),
    (re.compile(r"\bguide", re.I), "මාර්ගෝපදේශක සංචාරය"),
    (re.compile(r"\bexplore\b", re.I), "නැරඹීම"),
]


def translate_activity_phrase(phrase: str) -> str:
    key = phrase.strip().lower()
    if key in ACTIVITY_PHRASES_SI:
        return ACTIVITY_PHRASES_SI[key]
    for pattern, sinhala in KEYWORD_PHRASES_SI:
        if pattern.search(phrase):
            return sinhala
    return phrase.strip()  # unmatched: keep original English rather than guess


def activities_si(activities_field: str) -> str:
    """Translates a comma-separated activities field, deduplicating
    consecutive identical translations (several English phrases often map
    to the same Sinhala term, e.g. "Photography" and "Take photos")."""
    parts = [translate_activity_phrase(a) for a in activities_field.split(",")]
    deduped = []
    for part in parts:
        if not deduped or deduped[-1] != part:
            deduped.append(part)
    return ", ".join(deduped)
