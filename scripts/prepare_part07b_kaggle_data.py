"""Prepare the Part 7B corrective-training Kaggle Dataset folder."""

import hashlib
import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "data" / "training" / "corrective_v0.3.0"
OUTPUT = ROOT / "kaggle_upload" / "tripme-part07b-corrective-train"
FILES = (
    "combined_train_ai_reviewed.jsonl",
    "combined_validation_ai_reviewed.jsonl",
    "ai_review_summary.json",
    "quality_validation.json",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def count_jsonl(path: Path) -> int:
    return sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip())


def main():
    if OUTPUT.exists():
        shutil.rmtree(OUTPUT)
    OUTPUT.mkdir(parents=True)
    details = []
    for name in FILES:
        source = SOURCE / name
        if not source.is_file():
            raise FileNotFoundError(source)
        destination = OUTPUT / name
        shutil.copy2(source, destination)
        details.append({
            "name": name,
            "bytes": destination.stat().st_size,
            "sha256": sha256(destination),
            "rows": count_jsonl(destination) if destination.suffix == ".jsonl" else None,
        })
    metadata = {
        "title": "TripMe Part 07B Corrective QLoRA Data",
        "id": "YOUR_KAGGLE_USERNAME/tripme-part07b-corrective-train",
        "licenses": [{"name": "other"}],
    }
    (OUTPUT / "dataset-metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    manifest = {
        "status": "ready_for_corrective_training",
        "dataset_status": "ai_second_checked_candidate_requires_human_review",
        "train_rows": 1800,
        "validation_rows": 250,
        "files": details,
    }
    (OUTPUT / "upload_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))
    print(f"Prepared: {OUTPUT}")


if __name__ == "__main__":
    main()
