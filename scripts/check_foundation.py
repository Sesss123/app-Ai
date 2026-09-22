"""Validate the files and assumptions required by Roadmap Part 1.

Usage:
    python scripts/check_foundation.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
REQUIRED_FILES = (
    "PRODUCT_SCOPE_SI.md",
    "ROADMAP_PARTS_SI.md",
    "AI_MODEL_A_TO_Z_PLAN_SI.md",
    "requirements.txt",
    "requirements-training.txt",
    ".env.example",
    "config/project.json",
    "notebooks/finetune_kaggle.ipynb",
)
REQUIRED_DIRECTORIES = ("data/raw", "data/training", "notebooks", "scripts")
REQUIRED_CONFIG_SECTIONS = (
    "project",
    "reproducibility",
    "paths",
    "training",
    "quality_targets",
)


def fail(message: str, errors: list[str]) -> None:
    errors.append(message)
    print(f"[FAIL] {message}")


def main() -> None:
    errors: list[str] = []

    for relative in REQUIRED_FILES:
        path = ROOT / relative
        if path.is_file():
            print(f"[ OK ] file: {relative}")
        else:
            fail(f"missing file: {relative}", errors)

    for relative in REQUIRED_DIRECTORIES:
        path = ROOT / relative
        if path.is_dir():
            print(f"[ OK ] directory: {relative}")
        else:
            fail(f"missing directory: {relative}", errors)

    config_path = ROOT / "config" / "project.json"
    if config_path.is_file():
        try:
            config = json.loads(config_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            fail(f"invalid project config: {exc}", errors)
        else:
            for section in REQUIRED_CONFIG_SECTIONS:
                if section not in config:
                    fail(f"missing config section: {section}", errors)
            ratios = config.get("reproducibility", {})
            split_total = sum(
                float(ratios.get(key, 0))
                for key in ("train_ratio", "validation_ratio", "test_ratio")
            )
            if abs(split_total - 1.0) > 1e-9:
                fail(f"dataset split ratios total {split_total}, expected 1.0", errors)
            else:
                print("[ OK ] dataset split ratios total 1.0")
            seed = ratios.get("seed")
            if not isinstance(seed, int):
                fail("reproducibility.seed must be an integer", errors)
            else:
                print(f"[ OK ] reproducibility seed: {seed}")

    notebook_path = ROOT / "notebooks" / "finetune_kaggle.ipynb"
    if notebook_path.is_file():
        try:
            notebook = json.loads(notebook_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            fail(f"invalid notebook JSON: {exc}", errors)
        else:
            if notebook.get("nbformat") != 4 or not notebook.get("cells"):
                fail("training notebook has an invalid structure", errors)
            else:
                print(f"[ OK ] training notebook: {len(notebook['cells'])} cells")

    if errors:
        print(f"\nFoundation check failed with {len(errors)} error(s).")
        sys.exit(1)
    print("\nFoundation check passed. Roadmap Part 1 requirements are present.")


if __name__ == "__main__":
    main()

