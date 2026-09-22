"""Validate and import the Part 5 smoke-training output ZIP."""

import json
import shutil
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
ZIP_PATH = ROOT / "kaggle_results" / "part05" / "tripme_part05_smoke_output.zip"
DEST = ROOT / "artifacts" / "part05_smoke"
REQUIRED = {"adapter_config.json", "adapter_model.safetensors", "training_metrics.json", "smoke_manifest.json"}


def main() -> None:
    if not ZIP_PATH.is_file(): raise SystemExit(f"Missing {ZIP_PATH}")
    if DEST.exists(): shutil.rmtree(DEST)
    DEST.mkdir(parents=True)
    with zipfile.ZipFile(ZIP_PATH) as archive:
        names = {Path(name).name for name in archive.namelist() if not name.endswith("/")}
        missing = REQUIRED - names
        if missing: raise SystemExit(f"Invalid smoke output; missing {sorted(missing)}")
        archive.extractall(DEST)
    metrics_files = list(DEST.rglob("training_metrics.json")); manifest_files = list(DEST.rglob("smoke_manifest.json"))
    metrics = json.loads(metrics_files[0].read_text(encoding="utf-8"))
    manifest = json.loads(manifest_files[0].read_text(encoding="utf-8"))
    if manifest.get("status") != "smoke_complete" or not metrics.get("train_runtime"):
        raise SystemExit("Smoke manifest/metrics did not pass validation")
    print("Part 5 smoke output imported successfully.")
    print(json.dumps({"manifest": manifest, "metrics": metrics}, indent=2))


if __name__ == "__main__": main()

