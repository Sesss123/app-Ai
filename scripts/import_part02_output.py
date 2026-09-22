"""Validate and import the Part 2 ZIP downloaded from Kaggle.

Place ``tripme_part02_output.zip`` in ``kaggle_results/part02`` and run:
    python scripts/import_part02_output.py
"""

from __future__ import annotations

import json
import shutil
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
ZIP_PATH = ROOT / "kaggle_results" / "part02" / "tripme_part02_output.zip"
DESTINATION = ROOT / "reports" / "part02"
REQUIRED = {
    "raw_audit.json",
    "manual_review_queue.csv",
    "part02_summary.md",
    "part02_manifest.json",
}


def main() -> None:
    if not ZIP_PATH.is_file():
        raise SystemExit(f"Missing Kaggle output: {ZIP_PATH}")

    with zipfile.ZipFile(ZIP_PATH) as archive:
        names = {Path(name).name for name in archive.namelist() if not name.endswith("/")}
        missing = REQUIRED - names
        if missing:
            raise SystemExit(f"Invalid Part 2 output; missing: {sorted(missing)}")

        if DESTINATION.exists():
            shutil.rmtree(DESTINATION)
        DESTINATION.mkdir(parents=True)
        archive.extractall(DESTINATION)

    manifest_path = DESTINATION / "part02_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("part") != 2 or manifest.get("status") != "audit_complete":
        raise SystemExit("Part 2 manifest has an unexpected part/status value")

    report = json.loads((DESTINATION / "raw_audit.json").read_text(encoding="utf-8"))
    print("Part 2 Kaggle output imported successfully.")
    print(json.dumps(report.get("summary", {}), indent=2))
    print(f"Reports: {DESTINATION}")


if __name__ == "__main__":
    main()

