"""Import Part 8 results and compare the corrective adapter with Part 6."""

import json
import shutil
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
ZIP_PATH = ROOT / "kaggle_results" / "part08" / "tripme_part08_eval_output.zip"
OUTPUT = ROOT / "reports" / "part08" / "corrective_eval"
PART6_SUMMARY = ROOT / "reports" / "part06" / "provisional_eval" / "evaluation_summary.json"
REQUIRED = {"evaluation_summary.json", "corrective_generations.jsonl"}


def main():
    if not ZIP_PATH.is_file():
        raise FileNotFoundError(f"Place the Kaggle ZIP here: {ZIP_PATH}")
    with zipfile.ZipFile(ZIP_PATH) as archive:
        names = {Path(name).name for name in archive.namelist() if not name.endswith("/")}
        missing = REQUIRED - names
        if missing:
            raise ValueError(f"Missing files: {sorted(missing)}")
        if OUTPUT.exists():
            shutil.rmtree(OUTPUT)
        OUTPUT.mkdir(parents=True)
        archive.extractall(OUTPUT)
    summary = json.loads((OUTPUT / "evaluation_summary.json").read_text(encoding="utf-8"))
    rows = [json.loads(line) for line in (OUTPUT / "corrective_generations.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    if summary.get("status") != "part08_corrective_evaluation_complete_not_human_gold" or len(rows) != 120:
        raise ValueError("Unexpected Part 8 output")
    old = json.loads(PART6_SUMMARY.read_text(encoding="utf-8"))["adapter_all_120"]
    new = summary["all_120"]
    flagged = [row for row in rows if (
        not row["automatic_checks"]["complete_ending"]
        or row["automatic_checks"]["hit_token_limit"]
        or row["automatic_checks"]["place_name_coverage"] < 1.0
        or not row["automatic_checks"]["scenario_relevance"]
        or not row["automatic_checks"]["encoding_clean"]
        or row["automatic_checks"]["repetition_score"] > 0.15
    )]
    (OUTPUT / "human_review_queue.jsonl").write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in flagged) + ("\n" if flagged else ""), encoding="utf-8"
    )
    comparison = {
        "status": "part08_imported_part09_gate_pending",
        "rows": len(rows), "flagged_rows": len(flagged),
        "old_part06": old, "new_part08": new,
        "changes": {
            "complete_ending_rate": new["complete_ending_rate"] - old["complete_ending_rate"],
            "token_limit_hit_rate": new["token_limit_hit_rate"] - old["token_limit_hit_rate"],
            "place_name_coverage": new["mean_place_name_coverage"] - old["mean_place_name_coverage"],
            "repetition_score": new["mean_repetition_score"] - old["mean_repetition_score"],
        },
        "release_status": "human_review_and_part09_gate_required",
    }
    (OUTPUT / "import_summary.json").write_text(json.dumps(comparison, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(comparison, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
