"""Import the validated Part 2 cleaning output downloaded from Kaggle."""

import json
import shutil
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
ZIP_PATH = ROOT / "kaggle_results" / "part02_cleaning" / "tripme_part02_cleaning_output.zip"
REPORT_DIR = ROOT / "reports" / "part02_cleaning"
VERIFIED_DIR = ROOT / "data" / "verified"
REQUIRED = {"places_clean.jsonl", "manual_review_queue.csv", "cleaning_summary.json", "parse_errors.json"}


def main() -> None:
    if not ZIP_PATH.is_file():
        raise SystemExit(f"Missing: {ZIP_PATH}")
    temp = ROOT / ".part02_cleaning_import"
    if temp.exists():
        shutil.rmtree(temp)
    temp.mkdir()
    with zipfile.ZipFile(ZIP_PATH) as archive:
        names = {Path(name).name for name in archive.namelist() if not name.endswith("/")}
        missing = REQUIRED - names
        if missing:
            raise SystemExit(f"Invalid output; missing {sorted(missing)}")
        archive.extractall(temp)
    summary = json.loads((temp / "cleaning_summary.json").read_text(encoding="utf-8"))
    if summary.get("records", 0) <= 0 or summary.get("parse_errors") != 0:
        raise SystemExit(f"Cleaning output failed validation: {summary}")
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    VERIFIED_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(temp / "places_clean.jsonl", VERIFIED_DIR / "places_v0.1.0.jsonl")
    for name in REQUIRED - {"places_clean.jsonl"}:
        shutil.copy2(temp / name, REPORT_DIR / name)
    shutil.rmtree(temp)
    print("Part 2 cleaning output imported successfully.")
    print(json.dumps(summary, indent=2))
    print(f"Canonical dataset: {VERIFIED_DIR / 'places_v0.1.0.jsonl'}")


if __name__ == "__main__":
    main()

