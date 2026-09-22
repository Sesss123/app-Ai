"""Validate and import the Part 10 second corrective-training adapter."""

import json
import shutil
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
ZIP_PATH = ROOT / "kaggle_results" / "part10" / "tripme_part10_corrective_output.zip"
OUTPUT = ROOT / "artifacts" / "part10_corrective"
REPORT = ROOT / "reports" / "part10" / "training_result.json"
REQUIRED = {
    "adapter_config.json", "adapter_model.safetensors", "training_metrics.json",
    "training_manifest.json", "targeted_validation_generations.jsonl",
}


def main():
    if not ZIP_PATH.is_file():
        raise FileNotFoundError(ZIP_PATH)
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
    generations = [json.loads(line) for line in (OUTPUT / "targeted_validation_generations.jsonl").read_text(encoding="utf-8").splitlines() if line]
    if manifest.get("status") != "second_corrective_training_complete":
        raise ValueError(f"Unexpected status: {manifest.get('status')}")
    if (manifest.get("train_rows"), manifest.get("validation_rows")) != (2338, 340):
        raise ValueError("Unexpected training row counts")
    if manifest.get("training_origin") != "base_model_not_previous_adapter":
        raise ValueError("Unexpected training origin")
    if len(generations) != 20:
        raise ValueError(f"Expected 20 targeted generations, found {len(generations)}")

    flagged = []
    for row in generations:
        generated = row.get("generated", "")
        expected_names = [m["content"] for m in row.get("prompt_messages", []) if m.get("role") == "system"]
        reasons = []
        if not generated.strip(): reasons.append("empty")
        if row.get("hit_token_limit"): reasons.append("token_limit")
        if "\ufffd" in generated: reasons.append("replacement_character")
        if "{" in generated or "}" in generated: reasons.append("possible_placeholder")
        if reasons:
            flagged.append({"scenario": row.get("scenario"), "reasons": reasons, "generated": generated})
    result = {
        "status": "part10_adapter_imported_gold_evaluation_required",
        "artifact_dir": "artifacts/part10_corrective",
        "manifest": manifest,
        "metrics": metrics,
        "targeted_generation_rows": len(generations),
        "automatically_flagged_targeted_rows": len(flagged),
        "flagged_rows": flagged,
        "release_status": "not_for_production_gold_evaluation_required",
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
