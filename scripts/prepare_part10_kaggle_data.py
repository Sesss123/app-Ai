"""Prepare the second corrective-training Kaggle dataset and notebook."""

import hashlib
import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "data" / "training" / "corrective_v0.4.0"
OUTPUT = ROOT / "kaggle_upload" / "tripme-part10-corrective-train"
BASE_NOTEBOOK = ROOT / "notebooks" / "part07b_corrective_train_kaggle.ipynb"
NOTEBOOK = ROOT / "notebooks" / "part10_corrective_train_kaggle.ipynb"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    if OUTPUT.exists():
        shutil.rmtree(OUTPUT)
    OUTPUT.mkdir(parents=True)
    files = []
    for name in ("combined_train.jsonl", "combined_validation.jsonl", "summary.json"):
        source = SOURCE / name
        destination = OUTPUT / name
        shutil.copy2(source, destination)
        files.append({"name": name, "bytes": destination.stat().st_size, "sha256": digest(destination)})
    metadata = {
        "title": "TripMe Part 10 Second Corrective Training Data",
        "id": "YOUR_KAGGLE_USERNAME/tripme-part10-corrective-train",
        "licenses": [{"name": "other"}],
    }
    (OUTPUT / "dataset-metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    manifest = {
        "status": "ready_for_kaggle_training",
        "dataset_status": "ai_corrective_draft_requires_human_review",
        "train_rows": 2338,
        "validation_rows": 340,
        "files": files,
    }
    (OUTPUT / "upload_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    notebook = json.loads(BASE_NOTEBOOK.read_text(encoding="utf-8"))
    replacements = {
        "Part 7B — Corrective QLoRA Retraining": "Part 10 — Second Corrective QLoRA Retraining",
        "tripme-part07b-corrective-train": "tripme-part10-corrective-train",
        "combined_train_ai_reviewed.jsonl": "combined_train.jsonl",
        "combined_validation_ai_reviewed.jsonl": "combined_validation.jsonl",
        "assert len(data['train']) == 1800": "assert len(data['train']) == 2338",
        "assert len(data['validation']) == 250": "assert len(data['validation']) == 340",
        "tripme-corrective-run": "tripme-second-corrective-run",
        "tripme-corrective-adapter": "tripme-second-corrective-adapter",
        "tripme_part07b_corrective_output.zip": "tripme_part10_corrective_output.zip",
        "tripme_part07b_corrective_output": "tripme_part10_corrective_output",
        "corrective_training_complete": "second_corrective_training_complete",
        "ai_second_checked_candidate_requires_human_review": "ai_corrective_draft_requires_human_review",
        "target_scenarios = {'current_fact_refusal', 'budget_uncertainty', 'family_accessibility', 'culture_etiquette'}": "target_scenarios = {'current_fact_refusal', 'budget_uncertainty', 'current_uncertainty', 'family_accessibility', 'culture_etiquette', 'itinerary_place_retention', 'comparison'}",
        "reviewed 1,800/250 combined dataset": "2,338/340 combined corrective dataset",
    }
    for cell in notebook["cells"]:
        source = "".join(cell.get("source", []))
        for old, new in replacements.items():
            source = source.replace(old, new)
        cell["source"] = source.splitlines(keepends=True)
    NOTEBOOK.write_text(json.dumps(notebook, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(manifest, indent=2))
    print(f"Prepared: {OUTPUT}")
    print(f"Notebook: {NOTEBOOK}")


if __name__ == "__main__":
    main()
