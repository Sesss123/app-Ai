"""Prepare the second-checked pilot dataset for Kaggle QLoRA training."""

import hashlib
import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "data" / "training" / "pilot_v0.2.0" / "review"
OUTPUT = ROOT / "kaggle_upload" / "tripme-part05b-pilot-train"
FILES = (
    "second_checked_train_candidate.jsonl",
    "second_checked_validation_candidate.jsonl",
    "second_check_summary.json",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def count_jsonl(path: Path) -> int:
    return sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip())


def main() -> None:
    if OUTPUT.exists():
        shutil.rmtree(OUTPUT)
    OUTPUT.mkdir(parents=True)
    manifest_files = []
    for name in FILES:
        source = SOURCE / name
        if not source.is_file():
            raise FileNotFoundError(source)
        destination = OUTPUT / name
        shutil.copy2(source, destination)
        manifest_files.append({
            "name": name,
            "bytes": destination.stat().st_size,
            "sha256": sha256(destination),
            "rows": count_jsonl(destination) if destination.suffix == ".jsonl" else None,
        })

    metadata = {
        "title": "TripMe Part 05B Second-Checked Pilot Training Data",
        "id": "YOUR_KAGGLE_USERNAME/tripme-part05b-pilot-train",
        "licenses": [{"name": "other"}],
    }
    (OUTPUT / "dataset-metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    manifest = {
        "status": "ready_for_pilot_training",
        "review_status": "ai_second_checked_candidate_requires_human_review",
        "train_rows": 900,
        "validation_rows": 100,
        "files": manifest_files,
    }
    (OUTPUT / "upload_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))
    print(f"Prepared: {OUTPUT}")


if __name__ == "__main__":
    main()
