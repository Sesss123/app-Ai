"""Build the Kaggle input folder for Roadmap Part 2.

Usage:
    python scripts/prepare_part02_kaggle_data.py
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "kaggle_upload" / "tripme-part02-data"


def main() -> None:
    if OUTPUT.exists():
        shutil.rmtree(OUTPUT)
    (OUTPUT / "data").mkdir(parents=True)
    (OUTPUT / "scripts").mkdir(parents=True)

    shutil.copytree(ROOT / "data" / "raw", OUTPUT / "data" / "raw")
    shutil.copy2(ROOT / "scripts" / "00_audit_raw.py", OUTPUT / "scripts" / "00_audit_raw.py")

    raw_files = list((OUTPUT / "data" / "raw").rglob("*.jsonl"))
    metadata = {
        "title": "TripMe Part 02 Raw Data Audit",
        "id": "YOUR_KAGGLE_USERNAME/tripme-part02-data",
        "licenses": [{"name": "other"}],
    }
    (OUTPUT / "dataset-metadata.json").write_text(
        json.dumps(metadata, indent=2), encoding="utf-8"
    )
    print(f"Prepared: {OUTPUT}")
    print(f"Raw files: {len(raw_files)}")


if __name__ == "__main__":
    main()

