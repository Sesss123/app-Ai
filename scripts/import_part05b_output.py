"""Validate and import the Kaggle Part 5B pilot-training adapter."""

import json
import shutil
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
ZIP_PATH = ROOT / "kaggle_results" / "part05b" / "tripme_part05b_pilot_output.zip"
OUTPUT = ROOT / "artifacts" / "part05_pilot"
REPORT = ROOT / "reports" / "part05" / "pilot_training_result.json"
REQUIRED = {"adapter_config.json", "training_metrics.json", "training_manifest.json", "validation_generations.jsonl"}


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

    manifest = json.loads((OUTPUT / "training_manifest.json").read_text(encoding="utf-8"))
    metrics = json.loads((OUTPUT / "training_metrics.json").read_text(encoding="utf-8"))
    if manifest.get("status") != "pilot_training_complete":
        raise ValueError(f"Unexpected training status: {manifest.get('status')}")
    if manifest.get("train_rows") != 900 or manifest.get("validation_rows") != 100:
        raise ValueError("Unexpected train/validation row counts")

    generations = [
        json.loads(line)
        for line in (OUTPUT / "validation_generations.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    result = {
        "status": "pilot_adapter_imported",
        "artifact_dir": str(OUTPUT.relative_to(ROOT)),
        "manifest": manifest,
        "metrics": metrics,
        "validation_generation_rows": len(generations),
        "release_status": "evaluation_required_not_for_production",
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
