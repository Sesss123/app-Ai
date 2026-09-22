"""Validate and import the Part 7B corrective-training adapter."""

import json
import shutil
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
ZIP_PATH = ROOT / "kaggle_results" / "part07b" / "tripme_part07b_corrective_output.zip"
OUTPUT = ROOT / "artifacts" / "part07_corrective"
REPORT = ROOT / "reports" / "part07" / "corrective_training_result.json"
REQUIRED = {
    "adapter_config.json", "adapter_model.safetensors", "training_metrics.json",
    "training_manifest.json", "targeted_validation_generations.jsonl",
}


def main():
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
    generations = [
        json.loads(line)
        for line in (OUTPUT / "targeted_validation_generations.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if manifest.get("status") != "corrective_training_complete":
        raise ValueError(f"Unexpected status: {manifest.get('status')}")
    if manifest.get("train_rows") != 1800 or manifest.get("validation_rows") != 250:
        raise ValueError("Unexpected training row counts")
    if manifest.get("training_origin") != "base_model_not_previous_adapter":
        raise ValueError("Corrective model was not trained from the required base model origin")
    if len(generations) != 20:
        raise ValueError(f"Expected 20 targeted generations, found {len(generations)}")

    flagged = [
        row for row in generations
        if row.get("hit_token_limit")
        or not row.get("generated", "").strip()
        or "�" in row.get("generated", "")
    ]
    result = {
        "status": "corrective_adapter_imported_evaluation_required",
        "artifact_dir": str(OUTPUT.relative_to(ROOT)),
        "manifest": manifest,
        "metrics": metrics,
        "targeted_generation_rows": len(generations),
        "automatically_flagged_targeted_rows": len(flagged),
        "release_status": "part08_evaluation_required_not_for_production",
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
