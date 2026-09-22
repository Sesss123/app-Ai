import json
import re
from collections import Counter
from pathlib import Path


ROOT = Path(r"D:\app ai")
BASE = ROOT / "data" / "training" / "pilot_v0.2.0"
REVIEW_DIR = BASE / "review"
INPUTS = [BASE / "pilot_train_draft.jsonl", BASE / "pilot_validation_draft.jsonl"]
OUTPUTS = [
    REVIEW_DIR / "ai_reviewed_train_candidate.jsonl",
    REVIEW_DIR / "ai_reviewed_validation_candidate.jsonl",
]


def apply_replacements(text, replacements):
    for old, new in replacements:
        text = text.replace(old, new)
    return re.sub(r"\s+([,.])", r"\1", text).strip()


SI_USER = [
    ("accessibility අවශ්‍ය", "ප්‍රවේශ පහසුකම් අවශ්‍ය"),
]

SI_ANSWER = [
    ("Static context එකෙන්", "ලබාදී ඇති ස්ථිතික දත්ත අනුව"),
    ("Official හෝ recent dated source එකක්", "නිල හෝ මෑත දිනයක් සඳහන් මූලාශ්‍රයක්"),
    ("Exact order එක", "නිශ්චිත අනුපිළිවෙළ"),
    ("current opening hours", "වත්මන් විවෘත වේලාවන්"),
    ("සැබෑ travel distances mapping source එකකින්", "සැබෑ ගමන් දුර සිතියම් සේවාවකින්"),
    ("ලබාදී ඇති activities:", "දත්තවල සඳහන් ක්‍රියාකාරකම්:"),
    ("Current conditions වෙනම තහවුරු කරන්න.", "වත්මන් තත්ත්වය වෙනම මූලාශ්‍රයකින් තහවුරු කරන්න."),
    ("photography rules", "ඡායාරූප ගැනීමේ නීති"),
    ("official source එකකින්", "නිල මූලාශ්‍රයකින්"),
    ("current accessibility evidence", "ප්‍රවේශ පහසුකම් පිළිබඳ වත්මන් තහවුරු කළ තොරතුරු"),
    ("Entrances, toilets සහ parking", "පිවිසුම්, වැසිකිළි සහ වාහන නැවැත්වීමේ පහසුකම්"),
    ("නිල source එකකින්", "නිල මූලාශ්‍රයකින්"),
]

SINGLISH_ANSWER = [
    ("Static context eken", "Dila thiyena static data walin"),
    ("Official hari recent dated source ekak", "Official source ekak hari langadi date karapu source ekak"),
    ("Listed activities:", "Data eke thiyena activities:"),
    ("Current conditions wenama verify karanna.", "Danata thiyena thathwaya wenama source ekakin verify karanna."),
    ("Exact order ekata current opening hours saha real distances map source ekakin check karanna.",
     "Hari order eka hadanna kalin danata thiyena opening hours saha aththa gaman dura map source ekakin check karanna."),
    ("current accessibility evidence madi", "danata thiyena accessibility thorathuru madi"),
    ("Entrances, toilets saha parking official source ekakin verify karanna.",
     "Entrance, toilet saha parking pahasukam venue eken hari official source ekakin verify karanna."),
    ("photography rules check karanna", "photo ganna rules check karanna"),
    ("Special rules official source ekakin verify karanna.", "Vishesha rules official source ekakin verify karanna."),
]


def review_record(item, review_id):
    reviewed = json.loads(json.dumps(item, ensure_ascii=False))
    user_msg = next(m for m in reviewed["messages"] if m["role"] == "user")
    assistant_msg = next(m for m in reviewed["messages"] if m["role"] == "assistant")
    original_user = user_msg["content"]
    original_answer = assistant_msg["content"]
    lang = reviewed["lang"]

    if lang == "si":
        user_msg["content"] = apply_replacements(original_user, SI_USER)
        assistant_msg["content"] = apply_replacements(original_answer, SI_ANSWER)
        note = "Sinhala wording normalized; place names and factual safeguards preserved."
    elif lang == "singlish":
        user_msg["content"] = original_user.strip()
        assistant_msg["content"] = apply_replacements(original_answer, SINGLISH_ANSWER)
        note = "Singlish wording normalized; place names and factual safeguards preserved."
    else:
        user_msg["content"] = re.sub(r"\s+", " ", original_user).strip()
        assistant_msg["content"] = re.sub(r"(?<!\.)\.\.", ".", original_answer).strip()
        note = "No change required in AI first-pass."

    prompt_changed = user_msg["content"] != original_user
    answer_changed = assistant_msg["content"] != original_answer
    changed = prompt_changed or answer_changed
    decision = "Edit" if changed else "Approve"
    if changed and lang == "en":
        note = "Minor English punctuation cleanup; factual safeguards preserved."
    elif not changed:
        note = "No change required in AI first-pass."

    review = {
        "review_id": review_id,
        "decision": decision,
        "edited_prompt": user_msg["content"] if prompt_changed else "",
        "edited_answer": assistant_msg["content"] if answer_changed else "",
        "reviewer": "Codex AI first-pass",
        "notes": note,
        "lang": lang,
        "scenario": reviewed["scenario"],
    }
    reviewed["review_status"] = "ai_reviewed_candidate"
    reviewed["review_decision"] = decision
    return reviewed, review


def main():
    REVIEW_DIR.mkdir(parents=True, exist_ok=True)
    all_reviews = []
    global_index = 0
    output_counts = []

    for input_path, output_path in zip(INPUTS, OUTPUTS):
        items = [json.loads(line) for line in input_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        reviewed_items = []
        for item in items:
            global_index += 1
            reviewed, review = review_record(item, f"pilot-{global_index:04d}")
            reviewed_items.append(reviewed)
            all_reviews.append(review)
        output_path.write_text(
            "\n".join(json.dumps(row, ensure_ascii=False) for row in reviewed_items) + "\n",
            encoding="utf-8",
        )
        output_counts.append({"file": output_path.name, "rows": len(reviewed_items)})

    decisions = Counter(r["decision"] for r in all_reviews)
    languages = Counter(r["lang"] for r in all_reviews)
    scenarios = Counter(r["scenario"] for r in all_reviews)
    review_payload = {
        "status": "ai_reviewed_candidate_requires_human_review",
        "reviewer": "Codex AI first-pass",
        "total_rows": len(all_reviews),
        "decisions": dict(decisions),
        "languages": dict(languages),
        "scenarios": dict(scenarios),
        "outputs": output_counts,
        "reviews": all_reviews,
    }
    (REVIEW_DIR / "ai_review_records.json").write_text(
        json.dumps(review_payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (REVIEW_DIR / "ai_review_summary.json").write_text(
        json.dumps({k: v for k, v in review_payload.items() if k != "reviews"}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps({k: v for k, v in review_payload.items() if k != "reviews"}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
