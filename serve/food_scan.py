"""
Food photo identification - two models, used together.

1. A fine-tuned ViT classifier (see ../train_food_classifier_colab.ipynb),
   trained on ~2,500 crops merged from 4 Roboflow-sourced datasets.
   Closed-vocabulary (20 classes: 11 main dishes + string hoppers boost +
   milk_rice + 8 bakery/pastry items) but higher-precision *when* the dish
   is one of those 20, since it actually learned Sri Lankan dish
   appearances rather than guessing from general web-image associations.
2. CLIP zero-shot classification, open-vocabulary - we supply our own
   candidate dish list at inference time instead of being locked to a
   training-time label set (as Food-101-style classifiers are, none of
   which include Sri Lankan dishes). This is the fallback for anything
   outside the fine-tuned model's 20 classes.

identify_food() tries the fine-tuned model first; if it's confident, that
result wins (it's the more specialized model). Otherwise it falls back to
CLIP's broader vocabulary, since a low-confidence "must be one of these 20"
answer is worse than admitting the dish might be something else entirely.
"""

from functools import lru_cache
from pathlib import Path

CLIP_MODEL_NAME = "openai/clip-vit-base-patch32"

FINE_TUNED_MODEL_DIR = Path(__file__).resolve().parent / "sl-food-classifier"
FINE_TUNED_CONFIDENCE_THRESHOLD = 0.6  # below this, prefer CLIP's broader vocabulary instead

# Human-readable labels for the fine-tuned model's classes (its id2label in
# config.json uses training-folder-derived slugs like "dhal_curry").
FINE_TUNED_LABEL_DISPLAY = {
    "dhal_curry": "dhal curry",
    "donut": "donut",
    "egg_roll": "egg roll",
    "fish_bun": "fish bun",
    "fish_curry": "fish curry",
    "gotukola_mallum": "gotu kola mallum",
    "hoppers": "hoppers (appa)",
    "kiribath": "kiribath (milk rice)",
    "kottu": "kottu roti",
    "lunu_sambol": "lunu miris (onion sambol)",
    "milk_rice": "milk rice",
    "pastry": "pastry",
    "patis": "patties (patis)",
    "pittu": "pittu",
    "pol_sambol": "pol sambol",
    "sandwich": "sandwich",
    "sausage_bun": "sausage bun",
    "spanchi": "spanchi",
    "string_hoppers": "string hoppers (idiyappam)",
    "watalappam": "watalappam",
}

# Sri Lankan dishes first (this app's actual audience), general/international
# dishes appended as a fallback so a non-Sri-Lankan meal still gets a
# reasonable label instead of being forced into the wrong local dish name.
SRI_LANKAN_DISHES = [
    "kottu roti", "hoppers (appa)", "string hoppers (idiyappam)",
    "rice and curry", "dhal curry", "fish curry", "fish ambul thiyal", "pittu",
    "lamprais", "watalappam", "kiribath (milk rice)", "milk rice", "pol sambol",
    "gotu kola mallum", "lunu miris (onion sambol)",
    "egg hoppers", "vadai", "polos curry (young jackfruit)",
    "parippu (lentil curry)", "isso wade (shrimp fritters)",
    "achcharu (pickle)", "kavum (oil cake)",
    "fish bun", "sausage bun", "patties (patis)", "egg roll", "spanchi",
    "pastry", "donut",
]

GENERAL_DISHES = [
    "pizza", "sushi", "fried rice", "noodles", "burger", "salad",
    "grilled chicken", "pasta", "sandwich", "soup", "dessert/cake",
    "fruit platter", "bread", "curry (non-Sri Lankan)", "not food",
]

DEFAULT_LABELS = SRI_LANKAN_DISHES + GENERAL_DISHES


@lru_cache(maxsize=1)
def _get_clip_pipeline():
    from transformers import pipeline
    return pipeline("zero-shot-image-classification", model=CLIP_MODEL_NAME)


@lru_cache(maxsize=1)
def _get_fine_tuned_pipeline():
    if not FINE_TUNED_MODEL_DIR.is_dir():
        return None
    from transformers import pipeline
    return pipeline("image-classification", model=str(FINE_TUNED_MODEL_DIR))


def _identify_with_fine_tuned(image, top_k: int) -> list[dict] | None:
    """Returns [{"label": ..., "score": ...}, ...] using the fine-tuned
    model's own labels (mapped to display names), or None if that model
    isn't available (e.g. not downloaded/extracted into sl-food-classifier/)."""
    clf = _get_fine_tuned_pipeline()
    if clf is None:
        return None
    results = clf(image, top_k=top_k)
    return [
        {"label": FINE_TUNED_LABEL_DISPLAY.get(r["label"], r["label"]), "score": r["score"]}
        for r in results
    ]


def _identify_with_clip(image, labels: list[str] | None, top_k: int) -> list[dict]:
    clip = _get_clip_pipeline()
    candidate_labels = labels or DEFAULT_LABELS
    results = clip(image, candidate_labels=candidate_labels)
    return results[:top_k]


def identify_food(image, labels: list[str] | None = None, top_k: int = 3) -> list[dict]:
    """Classifies a food photo, preferring the fine-tuned Sri Lankan model
    when it's confident and falling back to open-vocabulary CLIP otherwise.

    `image` accepts anything transformers' image-classification pipelines
    accept: a PIL.Image, a file path, or a URL.

    Returns the top_k matches as [{"label": ..., "score": ...}, ...],
    sorted highest-confidence first. For the CLIP fallback path, confidence
    is relative to the label list given - a low top score (e.g. < 0.15)
    means none of the candidate labels fit well, worth surfacing to the
    user as "not sure" rather than confidently naming the wrong dish.
    """
    fine_tuned_results = _identify_with_fine_tuned(image, top_k)
    if fine_tuned_results and fine_tuned_results[0]["score"] >= FINE_TUNED_CONFIDENCE_THRESHOLD:
        return fine_tuned_results
    return _identify_with_clip(image, labels, top_k)
