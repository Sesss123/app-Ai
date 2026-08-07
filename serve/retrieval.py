"""
Plain-code retrieval over data/processed/places.json.

This deliberately does NOT use the LLM to search/filter places - it's a
direct lookup so that facts (price, hours, safety, district) stay reliable
even after fine-tuning. The LLM's job (see app.py) is to narrate the
shortlist this returns, not to invent or recall facts on its own.

Note: `lat`/`lng` in the source dataset are largely duplicated placeholders
(only 295 unique pairs across 1289 places), not reliable per-place GPS -
so filtering here is district-based, not distance-based.
"""

import json
import logging
from pathlib import Path

PLACES_PATH = Path(__file__).resolve().parent.parent / "data" / "processed" / "places.json"

_PLACES = []
_PLACES_BY_DISTRICT: dict = {}
DISTRICTS = []

try:
    with open(PLACES_PATH, encoding="utf-8") as _fh:
        _PLACES = json.load(_fh)
    
    for _p in _PLACES:
        _PLACES_BY_DISTRICT.setdefault(_p["district_id"], []).append(_p)
        
    DISTRICTS = sorted(_PLACES_BY_DISTRICT.keys())
except FileNotFoundError:
    logging.error(f"Dataset not found at {PLACES_PATH}. Please run the data preparation scripts first.")
except json.JSONDecodeError:
    logging.error(f"Failed to parse JSON dataset at {PLACES_PATH}.")
except Exception as e:
    logging.error(f"Error loading places dataset: {e}")


def find_places(
    district: str,
    category: str | None = None,
    budget_category: str | None = None,
    max_ticket_price: int | None = None,
    limit: int = 5,
) -> list[dict]:
    """Return up to `limit` place records matching the given filters.

    `district` should be one of DISTRICTS (case-insensitive match attempted).
    Other filters are optional; unmatched filters are simply ignored rather
    than raising, so a caller can pass best-effort parsed values.
    """
    candidates = _PLACES_BY_DISTRICT.get(district)
    if candidates is None:
        # try case-insensitive match
        for d in DISTRICTS:
            if d.lower() == district.lower():
                candidates = _PLACES_BY_DISTRICT[d]
                break
    if candidates is None:
        return []

    results = candidates
    if category:
        results = [p for p in results if p["category_id"].lower() == category.lower()]
    if budget_category:
        results = [p for p in results if p["budget_category"].lower() == budget_category.lower()]
    if max_ticket_price is not None:
        results = [p for p in results if p["ticket_price"] <= max_ticket_price]

    return results[:limit]


def get_place_by_id(place_id: str) -> dict | None:
    for p in _PLACES:
        if p["id"] == place_id:
            return p
    return None
