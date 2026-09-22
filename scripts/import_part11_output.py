"""Import Part 11, compare it with Parts 6 and 8, and build a review queue."""

import json
import shutil
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
ZIP_PATH = ROOT / "kaggle_results" / "part11" / "tripme_part11_eval_output.zip"
OUTPUT = ROOT / "reports" / "part11" / "evaluation"
PART6 = ROOT / "reports" / "part06" / "provisional_eval" / "evaluation_summary.json"
PART8 = ROOT / "reports" / "part08" / "corrective_eval" / "evaluation_summary.json"
REQUIRED = {"evaluation_summary.json", "corrective_generations.jsonl"}


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def main():
    with zipfile.ZipFile(ZIP_PATH) as archive:
        names = {Path(name).name for name in archive.namelist() if not name.endswith("/")}
        missing = REQUIRED - names
        if missing:
            raise ValueError(f"Missing files: {sorted(missing)}")
        if OUTPUT.exists():
            shutil.rmtree(OUTPUT)
        OUTPUT.mkdir(parents=True)
        archive.extractall(OUTPUT)
    summary = load_json(OUTPUT / "evaluation_summary.json")
    rows = [json.loads(line) for line in (OUTPUT / "corrective_generations.jsonl").read_text(encoding="utf-8").splitlines() if line]
    if summary.get("status") != "part11_corrective_evaluation_complete_not_human_gold" or len(rows) != 120:
        raise ValueError("Unexpected Part 11 output")
    part6 = load_json(PART6)["adapter_all_120"]
    part8 = load_json(PART8)["all_120"]
    current = summary["all_120"]
    flagged = []
    passed = []
    for row in rows:
        checks = row["automatic_checks"]
        reasons = []
        if not checks["complete_ending"]: reasons.append("incomplete_ending")
        if checks["hit_token_limit"]: reasons.append("token_limit")
        if checks["place_name_coverage"] < 1.0: reasons.append("place_name_coverage")
        if not checks["scenario_relevance"]: reasons.append("scenario_relevance")
        if not checks["encoding_clean"]: reasons.append("encoding")
        if checks["repetition_score"] > 0.15: reasons.append("repetition")
        review = {**row, "review_reasons": reasons, "review_priority": "flagged" if reasons else "sampled_pass"}
        (flagged if reasons else passed).append(review)
    sampled_pass = sorted(passed, key=lambda r: r["eval_id"])[:20]
    queue = flagged + sampled_pass
    (OUTPUT / "human_review_queue.jsonl").write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in queue) + "\n", encoding="utf-8"
    )
    keys = ["complete_ending_rate", "token_limit_hit_rate", "mean_place_name_coverage", "scenario_relevance_rate", "encoding_clean_rate", "mean_repetition_score"]
    report = {
        "status": "part11_imported_part12_gate_pending_part13_review_prepared",
        "rows": len(rows),
        "flagged_rows": len(flagged),
        "sampled_pass_rows": len(sampled_pass),
        "human_review_rows": len(queue),
        "part6": part6,
        "part8": part8,
        "part11": current,
        "change_part11_vs_part8": {key: current[key] - part8[key] for key in keys if key in part8},
        "change_part11_vs_part6": {key: current[key] - part6[key] for key in keys if key in part6},
    }
    (OUTPUT / "comparison.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
