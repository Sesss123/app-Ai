import json
import re
from collections import Counter
from pathlib import Path


ROOT = Path(r"D:\app ai")
BASE = ROOT / "data" / "training" / "pilot_v0.2.0"
REVIEW = BASE / "review"
ORIGINALS = [BASE / "pilot_train_draft.jsonl", BASE / "pilot_validation_draft.jsonl"]
FIRST_PASS = [REVIEW / "ai_reviewed_train_candidate.jsonl", REVIEW / "ai_reviewed_validation_candidate.jsonl"]
OUTPUTS = [REVIEW / "second_checked_train_candidate.jsonl", REVIEW / "second_checked_validation_candidate.jsonl"]

CATEGORY_SI = {
    "Buddhist Temple": "බෞද්ධ විහාරස්ථානය",
    "Temple": "ආගමික ස්ථානය",
    "Kovil": "කෝවිල",
    "Church": "දේවස්ථානය",
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
}

ACTIVITY_SI = {
    "prayer": "යාච්ඤා කිරීම",
    "photography": "ඡායාරූප ගැනීම",
    "meditation": "භාවනා කිරීම",
    "sightseeing": "ස්ථාන නැරඹීම",
    "exploring": "ගවේෂණය කිරීම",
    "learning": "ඉගෙනීම",
    "swimming": "පිහිනීම",
    "sunbathing": "හිරු එළියේ විවේක ගැනීම",
    "wildlife watching": "වනජීවීන් නැරඹීම",
    "walking": "ඇවිදීම",
    "rides": "විනෝද සවාරි",
    "family fun": "පවුලේ විනෝදය",
    "relaxing": "විවේක ගැනීම",
    "hiking": "පාගමන් යාම",
    "worship": "වන්දනා කිරීම",
}


def load_jsonl(path):
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]


def message(row, role):
    return next(m for m in row["messages"] if m["role"] == role)


def polish_si(text, *, is_system=False):
    replacements = [
        ("facts වලට", "ලබාදී ඇති කරුණුවලට"),
        (" facts පමණක්", " කරුණු පමණක්"),
        ("current facts", "වත්මන් තොරතුරු"),
        ("Context:", "පසුබිම් දත්ත:"),
        ("දැන් විවෘතද", "දැනට විවෘතද"),
        ("ප්‍රමාණවත් නැහැ", "ප්‍රමාණවත් නොවේ"),
        ("ගැන ස්ථානයෙන්", "පිළිබඳව අදාළ ස්ථානයෙන්"),
    ]
    for old, new in replacements:
        text = text.replace(old, new)

    for category, translated in sorted(CATEGORY_SI.items(), key=lambda x: -len(x[0])):
        text = text.replace(f"{category} ස්ථානයක් ලෙස", f"{translated}ක් ලෙස")
        text = text.replace(f"{category} ලෙස ලැයිස්තුගත", f"{translated}ක් ලෙස ලැයිස්තුගත")
        text = text.replace(f"{category} වර්ගයේ ස්ථානයකි", f"{translated}කි")
        text = text.replace(f"දිස්ත්‍රික්කයේ {category}.", f"දිස්ත්‍රික්කයේ {translated}කි.")

    marker = "දත්තවල සඳහන් ක්‍රියාකාරකම්:"
    if marker in text:
        prefix, activities = text.split(marker, 1)
        activity_text, sep, suffix = activities.partition(".")
        translated = ", ".join(ACTIVITY_SI.get(x.strip(), x.strip()) for x in activity_text.split(","))
        text = prefix + marker + " " + translated + (sep + suffix if sep else "")
    text = text.replace(".,", ",").replace("..", ".")
    return re.sub(r"\s+([,.])", r"\1", text).strip()


def polish_english(text):
    prefixes = [
        ("Without guessing ", "Without guessing, "),
        ("For planning purposes ", "For planning purposes, "),
        ("Using only supplied facts ", "Using only the supplied facts, "),
        ("For a practical trip ", "For a practical trip, "),
        ("For a family traveler ", "For a family traveler, "),
        ("In a clear answer ", ""),
        ("In a concise format ", ""),
    ]
    for old, new in prefixes:
        if text.startswith(old):
            text = new + text[len(old):]
            break
    suffixes = [
        (" give me an answer.", "."),
        (" state important limitations.", ". State the important limitations."),
        (" do not guess missing facts.", ". Do not guess missing facts."),
        (" stay within the supplied facts.", ". Use only the supplied facts."),
        (" keep the answer concise.", ". Keep the answer concise."),
        (" include necessary cautions.", ". Include necessary cautions."),
        (" help me decide.", ". Include the information needed to make a decision."),
    ]
    for old, new in suffixes:
        if text.endswith(old):
            text = text[:-len(old)] + new
            break
    text = re.sub(r"^([a-z])", lambda m: m.group(1).upper(), text)
    text = text.replace(".,", ",").replace("..", ".")
    return re.sub(r"\s+", " ", text).strip()


def second_pass(candidate):
    row = json.loads(json.dumps(candidate, ensure_ascii=False))
    lang = row["lang"]
    if lang == "si":
        for msg in row["messages"]:
            msg["content"] = polish_si(msg["content"], is_system=msg["role"] == "system")
    elif lang == "en":
        message(row, "user")["content"] = polish_english(message(row, "user")["content"])
        message(row, "assistant")["content"] = polish_english(message(row, "assistant")["content"])
    else:
        for msg in row["messages"]:
            msg["content"] = re.sub(r"\s+", " ", msg["content"]).replace(".,", ",").replace("..", ".").strip()
    row["review_status"] = "ai_second_checked_candidate"
    return row


def main():
    reviews = []
    global_index = 0
    for original_path, first_path, output_path in zip(ORIGINALS, FIRST_PASS, OUTPUTS):
        originals = load_jsonl(original_path)
        candidates = load_jsonl(first_path)
        assert len(originals) == len(candidates)
        outputs = []
        for original, candidate in zip(originals, candidates):
            global_index += 1
            final = second_pass(candidate)
            original_user = message(original, "user")["content"]
            original_answer = message(original, "assistant")["content"]
            final_user = message(final, "user")["content"]
            final_answer = message(final, "assistant")["content"]
            prompt_changed = final_user != original_user
            answer_changed = final_answer != original_answer
            decision = "Edit" if prompt_changed or answer_changed else "Approve"
            final["review_decision"] = decision
            reviews.append({
                "review_id": f"pilot-{global_index:04d}",
                "decision": decision,
                "edited_prompt": final_user if prompt_changed else "",
                "edited_answer": final_answer if answer_changed else "",
                "reviewer": "Codex AI second-pass",
                "notes": (
                    "Second-pass language and consistency corrections applied; place names and factual safeguards preserved."
                    if decision == "Edit" else
                    "Second-pass check found no change necessary."
                ),
                "lang": final["lang"],
                "scenario": final["scenario"],
            })
            outputs.append(final)
        output_path.write_text("\n".join(json.dumps(x, ensure_ascii=False) for x in outputs) + "\n", encoding="utf-8")

    payload = {
        "status": "ai_second_checked_candidate_requires_human_review",
        "reviewer": "Codex AI second-pass",
        "total_rows": len(reviews),
        "decisions": dict(Counter(x["decision"] for x in reviews)),
        "languages": dict(Counter(x["lang"] for x in reviews)),
        "scenarios": dict(Counter(x["scenario"] for x in reviews)),
        "reviews": reviews,
    }
    (REVIEW / "second_check_records.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    (REVIEW / "second_check_summary.json").write_text(
        json.dumps({k: v for k, v in payload.items() if k != "reviews"}, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps({k: v for k, v in payload.items() if k != "reviews"}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
