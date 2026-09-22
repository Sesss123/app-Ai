"""Prepare the input folder for the Part 2 cleaning Kaggle notebook."""

import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "kaggle_upload" / "tripme-part02-cleaning"


def main() -> None:
    if OUTPUT.exists():
        shutil.rmtree(OUTPUT)
    shutil.copytree(ROOT / "data" / "raw", OUTPUT / "data" / "raw")
    (OUTPUT / "scripts").mkdir(parents=True)
    shutil.copy2(ROOT / "scripts" / "part02_clean_places.py", OUTPUT / "scripts" / "part02_clean_places.py")
    metadata = {
        "title": "TripMe Part 02 Cleaning",
        "id": "YOUR_KAGGLE_USERNAME/tripme-part02-cleaning",
        "licenses": [{"name": "other"}],
    }
    (OUTPUT / "dataset-metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print(f"Prepared {OUTPUT}")


if __name__ == "__main__":
    main()

