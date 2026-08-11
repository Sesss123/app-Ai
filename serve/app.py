"""
FastAPI serving layer for TripMe AI mode.

Pipeline: audio in -> STT + language ID -> district/filter parsing ->
retrieval.find_places() -> fine-tuned LLM (grounded on the shortlist) ->
TTS -> audio out.

This file wires the pieces together behind /ask. The STT, LLM, and TTS
backends are loaded lazily (see the *_load functions) so the module can be
imported (e.g. for tests) without needing all three models available.

Run:
    uvicorn app:app --host 0.0.0.0 --port 8000
"""

import logging
import re
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from food_scan import identify_food
from retrieval import DISTRICTS, find_places

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("tripme")

app = FastAPI(title="TripMe AI Mode API")

# ---------------------------------------------------------------------------
# Config - adjust to match where you deploy the fine-tuned model/adapters.
# ---------------------------------------------------------------------------

LLM_MODEL_PATH = Path(__file__).resolve().parent.parent / "models" / "tripme-llama3-sinhala-q4_k_m.gguf"
WHISPER_MODEL_SIZE = "small"  # faster-whisper model size; "small" balances speed/accuracy for Sinhala/Tamil/English

SYSTEM_PROMPT_EN = (
    "You are TripMe, a warm and knowledgeable Sri Lankan travel voice assistant. "
    "Reply naturally in English, using only the facts provided about each place."
)
SYSTEM_PROMPT_SI = (
    "ඔබ TripMe නම් වූ, ශ්‍රී ලංකාවේ සංචාරක ස්ථාන පිළිබඳ නිර්දේශ ලබා දෙන කථන සහායකයෙකි. "
    "ලබා දී ඇති කරුණු පමණක් භාවිතා කරමින්, පිරිසිදු හා විධිමත් සිංහල භාෂාවෙන් "
    "ස්වාභාවිකව හා උණුසුම්ව පිළිතුරු දෙන්න."
)

SYSTEM_PROMPTS = {"en": SYSTEM_PROMPT_EN, "si": SYSTEM_PROMPT_SI}

_llm = None
_whisper = None
_tts = None


def get_llm():
    global _llm
    if _llm is None:
        from llama_cpp import Llama
        if not LLM_MODEL_PATH.exists():
            raise RuntimeError(
                f"LLM model not found at {LLM_MODEL_PATH}. Run the fine-tuning "
                "notebook, merge + export to GGUF, and place it here."
            )
        _llm = Llama(model_path=str(LLM_MODEL_PATH), n_ctx=2048, n_threads=4)
    return _llm


def get_whisper():
    global _whisper
    if _whisper is None:
        from faster_whisper import WhisperModel
        _whisper = WhisperModel(WHISPER_MODEL_SIZE, compute_type="int8")
    return _whisper


def get_tts():
    global _tts
    if _tts is None:
        raise RuntimeError(
            "TTS backend not configured. Sinhala/Tamil TTS coverage needs to be "
            "evaluated (see project plan, Step 5) before wiring a specific "
            "provider here - this is a known open item, not a bug."
        )
    return _tts


# ---------------------------------------------------------------------------
# Request/response models
# ---------------------------------------------------------------------------

class AskTextRequest(BaseModel):
    """Text-only request, for local testing without audio/STT/TTS."""
    question: str
    district: str
    lang: str = "en"  # "en" or "si"
    category: Optional[str] = None
    budget_category: Optional[str] = None
    max_ticket_price: Optional[int] = None


class AskResponse(BaseModel):
    transcript: str
    detected_language: str
    district: str
    place_ids: list[str]
    answer_text: str


class FoodMatch(BaseModel):
    label: str
    score: float


class ScanFoodResponse(BaseModel):
    matches: list[FoodMatch]


# ---------------------------------------------------------------------------
# Core pipeline pieces
# ---------------------------------------------------------------------------

def transcribe(audio_path: str) -> tuple[str, str]:
    """Returns (transcript, detected_language_code)."""
    whisper = get_whisper()
    segments, info = whisper.transcribe(audio_path)
    transcript = " ".join(seg.text.strip() for seg in segments)
    return transcript, info.language


def generate_answer(question: str, places: list[dict], lang: str = "en") -> str:
    """Calls the fine-tuned LLM, grounded on the given shortlist of places.

    The shortlist (from retrieval.find_places) is what keeps facts reliable;
    we pass it into the prompt so the model narrates real records instead of
    relying purely on what it memorized during fine-tuning.

    `lang` selects the system prompt (and therefore the response language,
    per the fine-tuning data) - "en" or "si". Falls back to English for any
    other/unrecognized language code (e.g. Tamil, not yet trained).
    """
    llm = get_llm()
    system_prompt = SYSTEM_PROMPTS.get(lang, SYSTEM_PROMPT_EN)

    places_context = "\n".join(
        f"- {p['name']} ({p['category_id']}, {p['district_id']}): {p['description']} "
        f"[budget: {p['budget_category']}, price: {p['ticket_price']} LKR, "
        f"safety: {p['safety_level']}, best time: {p['best_time_to_visit']}]"
        for p in places
    )
    user_content = f"{question}\n\nRelevant places:\n{places_context}" if places else question

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_content},
    ]
    result = llm.create_chat_completion(messages=messages, max_tokens=300, temperature=0.7)
    return result["choices"][0]["message"]["content"].strip()


def parse_district(text: str) -> Optional[str]:
    """Best-effort district extraction from free text using word boundaries.
    Real deployments should prefer passing district explicitly from app-side
    GPS/location state rather than relying on this."""
    lowered = text.lower()
    for district in DISTRICTS:
        # Use regex word boundaries (\b) to avoid partial matches
        pattern = r'\b' + re.escape(district.lower()) + r'\b'
        if re.search(pattern, lowered):
            return district
    return None


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/health")
def health():
    return {"status": "ok", "districts_loaded": len(DISTRICTS)}


@app.post("/ask/text", response_model=AskResponse)
def ask_text(req: AskTextRequest):
    """Text-in/text-out variant for local testing - skips STT/TTS."""
    places = find_places(
        district=req.district,
        category=req.category,
        budget_category=req.budget_category,
        max_ticket_price=req.max_ticket_price,
    )
    answer = generate_answer(req.question, places, lang=req.lang)
    return AskResponse(
        transcript=req.question,
        detected_language=req.lang,
        district=req.district,
        place_ids=[p["id"] for p in places],
        answer_text=answer,
    )


@app.post("/scan-food", response_model=ScanFoodResponse)
async def scan_food(photo: UploadFile = File(...)):
    """Identifies a dish from a photo via CLIP zero-shot classification -
    a separate vision model from the fine-tuned text-only TripMe LLM, since
    no pretrained Sri Lankan food classifier exists to fine-tune from (see
    food_scan.py for why zero-shot was chosen over a fixed-class model)."""
    import io

    from PIL import Image

    image_bytes = await photo.read()
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")

    results = identify_food(image)
    return ScanFoodResponse(matches=[FoodMatch(label=r["label"], score=r["score"]) for r in results])


@app.post("/ask")
async def ask(
    audio: UploadFile = File(...),
    district: Optional[str] = Form(None),
):
    """Full pipeline: audio -> STT -> retrieval -> LLM -> (TTS not yet wired,
    see get_tts()). Returns text for now; add audio synthesis once a
    Sinhala/Tamil-capable TTS backend is selected."""
    import tempfile

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp.write(await audio.read())
        tmp_path = tmp.name

    try:
        transcript, detected_lang = transcribe(tmp_path)
    finally:
        Path(tmp_path).unlink(missing_ok=True)

    resolved_district = district or parse_district(transcript)
    if resolved_district is None:
        return JSONResponse(
            status_code=400,
            content={"error": "Could not determine district from audio or request; "
                               "pass `district` explicitly from app-side location state."},
        )

    places = find_places(district=resolved_district)
    answer = generate_answer(transcript, places, lang=detected_lang)

    logger.info("district=%s lang=%s transcript=%r place_ids=%s",
                resolved_district, detected_lang, transcript, [p["id"] for p in places])

    return AskResponse(
        transcript=transcript,
        detected_language=detected_lang,
        district=resolved_district,
        place_ids=[p["id"] for p in places],
        answer_text=answer,
    )
