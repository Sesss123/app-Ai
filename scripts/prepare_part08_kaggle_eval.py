"""Prepare the corrective adapter for Part 8 on the same Part 6 sample."""

import json
import runpy
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
PART6_OUTPUT = ROOT / "kaggle_upload" / "tripme-part06-provisional-eval"
OUTPUT = ROOT / "kaggle_upload" / "tripme-part08-corrective-eval"
CORRECTIVE_ADAPTER = ROOT / "artifacts" / "part07_corrective"


def main():
    runpy.run_path(str(ROOT / "scripts" / "prepare_part06_kaggle_eval.py"), run_name="__main__")
    if OUTPUT.exists():
        shutil.rmtree(OUTPUT)
    shutil.move(str(PART6_OUTPUT), str(OUTPUT))
    shutil.rmtree(OUTPUT / "adapter")
    shutil.copytree(CORRECTIVE_ADAPTER, OUTPUT / "adapter")

    metadata = {
        "title": "TripMe Part 08 Corrective Adapter Evaluation",
        "id": "YOUR_KAGGLE_USERNAME/tripme-part08-corrective-eval",
        "licenses": [{"name": "other"}],
    }
    (OUTPUT / "dataset-metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    manifest = json.loads((OUTPUT / "package_manifest.json").read_text(encoding="utf-8"))
    manifest.update({
        "status": "part08_corrective_eval_ready_not_human_gold",
        "adapter_source": "artifacts/part07_corrective",
        "comparison_sample": "identical_to_part06_seed_42_sample",
    })
    (OUTPUT / "package_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    print(f"Prepared: {OUTPUT}")


if __name__ == "__main__":
    main()
