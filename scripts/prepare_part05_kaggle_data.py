"""Prepare the Part 5 smoke-training Kaggle Dataset folder."""

import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "data" / "training" / "pilot_v0.2.0"
OUTPUT = ROOT / "kaggle_upload" / "tripme-part05-smoke"
FILES = ("pilot_train_draft.jsonl", "pilot_validation_draft.jsonl", "generation_summary.json", "quality_validation.json")


def main() -> None:
    if OUTPUT.exists(): shutil.rmtree(OUTPUT)
    OUTPUT.mkdir(parents=True)
    for name in FILES:
        shutil.copy2(SOURCE / name, OUTPUT / name)
    metadata = {"title": "TripMe Part 05 QLoRA Smoke Data", "id": "YOUR_KAGGLE_USERNAME/tripme-part05-smoke", "licenses": [{"name": "other"}]}
    (OUTPUT / "dataset-metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print(f"Prepared {OUTPUT}")


if __name__ == "__main__": main()

