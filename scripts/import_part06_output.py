"""Import and validate the Part 6 provisional evaluation result."""

import json
import shutil
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
ZIP_PATH = ROOT / "kaggle_results" / "part06" / "tripme_part06_eval_output.zip"
OUTPUT = ROOT / "reports" / "part06" / "provisional_eval"
REQUIRED = {"evaluation_summary.json", "adapter_generations.jsonl", "base_generations_30.jsonl"}


def load_jsonl(path: Path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> None:
    if not ZIP_PATH.is_file():
        raise FileNotFoundError(f"Place the Kaggle ZIP here: {ZIP_PATH}")
    with zipfile.ZipFile(ZIP_PATH) as archive:
        names = {Path(name).name for name in archive.namelist() if not name.endswith("/")}
        missing = REQUIRED - names
        if missing:
            raise ValueError(f"Output ZIP is missing: {sorted(missing)}")
        if OUTPUT.exists():
            shutil.rmtree(OUTPUT)
        OUTPUT.mkdir(parents=True)
        archive.extractall(OUTPUT)

    summary = json.loads((OUTPUT / "evaluation_summary.json").read_text(encoding="utf-8"))
    adapter = load_jsonl(OUTPUT / "adapter_generations.jsonl")
    base = load_jsonl(OUTPUT / "base_generations_30.jsonl")
    if summary.get("status") != "provisional_evaluation_complete_not_human_gold":
        raise ValueError(f"Unexpected status: {summary.get('status')}")
    if len(adapter) != 120 or len(base) != 30:
        raise ValueError(f"Unexpected row counts: adapter={len(adapter)}, base={len(base)}")
    if any(row.get("evaluation_status") != "provisional_ai_draft_not_human_gold" for row in adapter):
        raise ValueError("Evaluation status label is missing")

    flagged = [
        row for row in adapter
        if row["automatic_checks"]["hit_token_limit"]
        or not row["automatic_checks"]["complete_ending"]
        or row["automatic_checks"]["place_name_coverage"] < 1.0
        or not row["automatic_checks"]["refusal_compliance"]
        or row["automatic_checks"]["repetition_score"] > 0.15
    ]
    review_path = OUTPUT / "human_review_queue.jsonl"
    review_path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in flagged) + ("\n" if flagged else ""),
        encoding="utf-8",
    )
    import_summary = {
        "status": "part06_imported_human_review_required",
        "adapter_rows": len(adapter),
        "base_rows": len(base),
        "automatically_flagged_rows": len(flagged),
        "evaluation_summary": summary,
    }
    (OUTPUT / "import_summary.json").write_text(
        json.dumps(import_summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(import_summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
