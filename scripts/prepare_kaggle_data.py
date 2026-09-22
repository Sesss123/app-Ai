"""Prepare the minimal Kaggle Dataset used by the training notebook.

Run from the project root:
    python scripts/prepare_kaggle_data.py

The resulting ``kaggle_upload/tripme-data`` directory can be uploaded as a
private Kaggle Dataset. Raw place files are intentionally not included.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SOURCE_DIR = ROOT / "data" / "training"
OUTPUT_DIR = ROOT / "kaggle_upload" / "tripme-data"
FILES = ("train_si.jsonl", "val_si.jsonl")


def validate_jsonl(path: Path) -> int:
    count = 0
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            record = json.loads(line)
            messages = record.get("messages")
            if not isinstance(messages, list) or not messages:
                raise ValueError(f"{path}:{line_number}: missing messages list")
            if any("role" not in item or "content" not in item for item in messages):
                raise ValueError(f"{path}:{line_number}: invalid message")
            count += 1
    return count


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    summary = {}
    for filename in FILES:
        source = SOURCE_DIR / filename
        if not source.is_file():
            raise FileNotFoundError(source)
        summary[filename] = validate_jsonl(source)
        shutil.copy2(source, OUTPUT_DIR / filename)

    metadata = {
        "title": "TripMe Sinhala Training Data",
        "id": "YOUR_KAGGLE_USERNAME/tripme-data",
        "licenses": [{"name": "other"}],
    }
    (OUTPUT_DIR / "dataset-metadata.json").write_text(
        json.dumps(metadata, indent=2), encoding="utf-8"
    )
    (OUTPUT_DIR / "data-summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    print(f"Prepared {OUTPUT_DIR}")
    for filename, count in summary.items():
        print(f"  {filename}: {count:,} examples")


if __name__ == "__main__":
    main()
