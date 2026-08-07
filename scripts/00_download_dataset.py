"""
Downloads the 6 TripMe place-category JSON files from the shared Google Drive
folder into data/raw/.

Usage:
    pip install gdown
    python scripts/00_download_dataset.py
"""

from pathlib import Path

import gdown

FOLDER_URL = "https://drive.google.com/drive/folders/1MTw7_6_qEqdL5vPTRGJ2INaVjVyKTkns"
RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    gdown.download_folder(url=FOLDER_URL, output=str(RAW_DIR), quiet=False, use_cookies=False)

    files = sorted(RAW_DIR.glob("*.json"))
    if not files:
        raise SystemExit(
            f"No JSON files landed in {RAW_DIR}. The Drive folder may not be "
            "shared as 'Anyone with the link' - check sharing settings and rerun."
        )

    print(f"\nDownloaded {len(files)} file(s) to {RAW_DIR}:")
    for f in files:
        print(f"  - {f.name} ({f.stat().st_size / 1024:.1f} KB)")


if __name__ == "__main__":
    main()
