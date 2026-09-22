"""Build a repeat gold evaluation package for the Part 10 adapter."""

import json
import runpy
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
BASE_PACKAGE = ROOT / "kaggle_upload" / "tripme-part06-provisional-eval"
OUTPUT = ROOT / "kaggle_upload" / "tripme-part11-corrective-eval"
ADAPTER = ROOT / "artifacts" / "part10_corrective"
BASE_NOTEBOOK = ROOT / "notebooks" / "part08_corrective_gold_eval_kaggle.ipynb"
NOTEBOOK = ROOT / "notebooks" / "part11_corrective_gold_eval_kaggle.ipynb"


def main():
    if not ADAPTER.is_dir():
        raise FileNotFoundError("Import Part 10 before preparing Part 11")
    runpy.run_path(str(ROOT / "scripts" / "prepare_part06_kaggle_eval.py"), run_name="__main__")
    if OUTPUT.exists():
        shutil.rmtree(OUTPUT)
    shutil.move(str(BASE_PACKAGE), str(OUTPUT))
    shutil.rmtree(OUTPUT / "adapter")
    shutil.copytree(ADAPTER, OUTPUT / "adapter")
    metadata = {
        "title": "TripMe Part 11 Second Corrective Gold Evaluation",
        "id": "YOUR_KAGGLE_USERNAME/tripme-part11-corrective-eval",
        "licenses": [{"name": "other"}],
    }
    (OUTPUT / "dataset-metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    manifest = json.loads((OUTPUT / "package_manifest.json").read_text(encoding="utf-8"))
    manifest.update({
        "status": "part11_repeat_gold_eval_ready_not_human_gold",
        "adapter_source": "artifacts/part10_corrective",
        "comparison_sample": "identical_to_part06_and_part08_seed_42_sample",
    })
    (OUTPUT / "package_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    notebook = json.loads(BASE_NOTEBOOK.read_text(encoding="utf-8"))
    replacements = {
        "Part 8": "Part 11",
        "part08": "part11",
        "tripme-part08-corrective-eval": "tripme-part11-corrective-eval",
        "tripme_part08_eval_output.zip": "tripme_part11_eval_output.zip",
        "tripme_part08_eval_output": "tripme_part11_eval_output",
    }
    for cell in notebook["cells"]:
        source = "".join(cell.get("source", []))
        for old, new in replacements.items():
            source = source.replace(old, new)
        cell["source"] = source.splitlines(keepends=True)
    NOTEBOOK.write_text(json.dumps(notebook, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    print(f"Prepared: {OUTPUT}")
    print(f"Notebook: {NOTEBOOK}")


if __name__ == "__main__":
    main()
