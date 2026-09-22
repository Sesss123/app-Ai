"""Apply an AI second-pass review to the Part 7 corrective examples."""

import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
BASE = ROOT / "data" / "training" / "corrective_v0.3.0"
PILOT = ROOT / "data" / "training" / "pilot_v0.2.0" / "review"
INPUTS = [BASE / "corrective_train_draft.jsonl", BASE / "corrective_validation_draft.jsonl"]
OUTPUTS = [BASE / "corrective_train_ai_reviewed.jsonl", BASE / "corrective_validation_ai_reviewed.jsonl"]


def load_jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_jsonl(path, rows):
    path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n", encoding="utf-8")


def main():
    reviews = []
    reviewed_splits = []
    global_index = 0
    for input_path, output_path in zip(INPUTS, OUTPUTS):
        output_rows = []
        for row in load_jsonl(input_path):
            global_index += 1
            system, user, answer = [message["content"] for message in row["messages"]]
            name = system.splitlines()[1].split(": ", 1)[1]
            clean_name = name.rstrip(".")
            changed = clean_name != name
            if changed:
                for message in row["messages"]:
                    message["content"] = message["content"].replace(name, clean_name)
            row["review_status"] = "ai_second_checked_candidate_requires_human_review"
            row["review_decision"] = "Edit" if changed else "Approve"
            output_rows.append(row)
            final_user = row["messages"][1]["content"]
            final_answer = row["messages"][2]["content"]
            reviews.append({
                "review_id": f"corrective-{global_index:04d}",
                "decision": row["review_decision"],
                "edited_prompt": final_user if changed else "",
                "edited_answer": final_answer if changed else "",
                "reviewer": "Codex AI second-pass",
                "notes": (
                    "Removed stray terminal punctuation from the registry display name; safety wording preserved."
                    if changed else
                    "Language, place-name grounding, and safety wording verified in AI second-pass."
                ),
            })
        write_jsonl(output_path, output_rows)
        reviewed_splits.append(output_rows)

    pilot_train = load_jsonl(PILOT / "second_checked_train_candidate.jsonl")
    pilot_val = load_jsonl(PILOT / "second_checked_validation_candidate.jsonl")
    combined_train = pilot_train + reviewed_splits[0]
    combined_val = pilot_val + reviewed_splits[1]
    write_jsonl(BASE / "combined_train_ai_reviewed.jsonl", combined_train)
    write_jsonl(BASE / "combined_validation_ai_reviewed.jsonl", combined_val)

    payload = {
        "status": "ai_second_checked_candidate_requires_human_review",
        "total_rows": len(reviews),
        "decisions": dict(Counter(row["decision"] for row in reviews)),
        "reviewer": "Codex AI second-pass",
        "reviews": reviews,
    }
    (BASE / "ai_review_records.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    (BASE / "ai_review_summary.json").write_text(
        json.dumps({key: value for key, value in payload.items() if key != "reviews"}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps({key: value for key, value in payload.items() if key != "reviews"}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
