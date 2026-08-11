"""
Run this after a Kaggle "Save & Run All (Commit)" shows COMPLETE for
notebooks/finetune_kaggle.ipynb, to advance to the next chunk with one
command instead of manual download -> dataset upload -> notebook push.

Usage:
    python scripts/kaggle_next_chunk.py

What it does:
1. Downloads the just-completed kernel's output (tripme-adapter/,
   chunk_state.json) from nohahamster/tripme-finetune.
2. Creates or updates the nohahamster/tripme-checkpoint Kaggle Dataset from
   that output.
3. Re-pushes notebooks/finetune_kaggle.ipynb as a fresh kernel version with
   both tripme-data and tripme-checkpoint attached as inputs, and GPU T4x2
   set explicitly (machine_shape) - the default accelerator Kaggle assigns
   otherwise has been an incompatible P100 in this project, which crashes
   bitsandbytes.

You still have to open the Kaggle notebook in a browser and click
"Run All", then when it finishes a chunk, click Save Version -> "Save & Run
All (Commit)" and wait for COMPLETE - that part cannot be automated (Kaggle
has no API for a notebook to trigger its own commit). This script only
automates everything that happens *after* that commit completes.
"""

import json
import os
import shutil
import sys
from pathlib import Path

os.environ.setdefault("PYTHONIOENCODING", "utf-8")

# The installed kaggle package's kernels_output() writes a log file without
# forcing utf-8, which raises UnicodeEncodeError on Windows (cp1252) if the
# log contains non-ASCII output (e.g. the Sinhala eval prompts) - patch
# open() so that write succeeds instead of aborting the download partway
# through, before any of the actual output files got pulled down.
import builtins

_orig_open = builtins.open


def _utf8_open(file, mode="r", *args, **kwargs):
    if "b" not in mode and "encoding" not in kwargs:
        kwargs["encoding"] = "utf-8"
    return _orig_open(file, mode, *args, **kwargs)


builtins.open = _utf8_open

from kaggle.api.kaggle_api_extended import KaggleApi  # noqa: E402

KERNEL = "nohahamster/tripme-finetune"
CHECKPOINT_DATASET = "nohahamster/tripme-checkpoint"
DATA_DATASET = "nohahamster/tripme-data"
PROJECT_ROOT = Path(__file__).resolve().parent.parent
NOTEBOOK_PATH = PROJECT_ROOT / "notebooks" / "finetune_kaggle.ipynb"
STAGING_DIR = PROJECT_ROOT / ".kaggle_staging"


def main():
    api = KaggleApi()
    api.authenticate()

    status = api.kernels_status(KERNEL)
    print(f"Kernel status: {status}")

    output_dir = STAGING_DIR / "checkpoint_output"
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True)

    print(f"\nDownloading output from {KERNEL}...")
    outfiles, _token = api.kernels_output(KERNEL, path=str(output_dir), force=True)
    downloaded = list(output_dir.rglob("*"))
    downloaded_files = [p for p in downloaded if p.is_file()]
    print(f"Downloaded {len(downloaded_files)} file(s):")
    for p in downloaded_files:
        print(f"  {p.relative_to(output_dir)} ({p.stat().st_size / 1e6:.1f} MB)")

    adapter_dir = output_dir / "tripme-adapter"
    chunk_state_file = output_dir / "chunk_state.json"
    if not adapter_dir.is_dir() or not chunk_state_file.is_file():
        print(
            "\nERROR: expected tripme-adapter/ and chunk_state.json in the "
            "downloaded output, but didn't find both. This usually means "
            "the Save & Run All commit hasn't finished yet, or it failed - "
            "check the kernel status/logs on kaggle.com before re-running "
            "this script."
        )
        sys.exit(1)

    chunk_state = json.loads(chunk_state_file.read_text(encoding="utf-8"))
    print(f"\nchunk_state.json: {chunk_state}")

    dataset_dir = STAGING_DIR / "checkpoint_dataset"
    if dataset_dir.exists():
        shutil.rmtree(dataset_dir)
    shutil.copytree(adapter_dir, dataset_dir / "tripme-adapter")
    shutil.copy(chunk_state_file, dataset_dir / "chunk_state.json")

    dataset_ref = CHECKPOINT_DATASET
    existing = api.dataset_list(search=CHECKPOINT_DATASET.split("/")[1], user=CHECKPOINT_DATASET.split("/")[0])
    exists = any(str(d.ref) == dataset_ref for d in existing)

    if exists:
        print(f"\nUpdating existing dataset {dataset_ref}...")
        api.dataset_create_version(
            str(dataset_dir), version_notes=f"chunk_state next_chunk={chunk_state.get('next_chunk')}", dir_mode="zip"
        )
    else:
        print(f"\nCreating new dataset {dataset_ref}...")
        metadata = {
            "title": "tripme-checkpoint",
            "id": dataset_ref,
            "licenses": [{"name": "CC0-1.0"}],
        }
        (dataset_dir / "dataset-metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
        api.dataset_create_new(str(dataset_dir), dir_mode="zip")

    print(f"\nRe-pushing {NOTEBOOK_PATH.name} with tripme-data + tripme-checkpoint attached...")
    kernel_push_dir = STAGING_DIR / "kernel_push"
    if kernel_push_dir.exists():
        shutil.rmtree(kernel_push_dir)
    kernel_push_dir.mkdir(parents=True)
    shutil.copy(NOTEBOOK_PATH, kernel_push_dir / NOTEBOOK_PATH.name)

    kernel_metadata = {
        "id": KERNEL,
        "title": KERNEL.split("/")[1],
        "code_file": NOTEBOOK_PATH.name,
        "language": "python",
        "kernel_type": "notebook",
        "is_private": True,
        "enable_gpu": True,
        "enable_internet": True,
        "dataset_sources": [DATA_DATASET, dataset_ref],
        "competition_sources": [],
        "kernel_sources": [],
        "machine_shape": "GPU_T4X2",
    }
    (kernel_push_dir / "kernel-metadata.json").write_text(json.dumps(kernel_metadata, indent=2), encoding="utf-8")

    api.kernels_push(str(kernel_push_dir))

    print(
        f"\nDone. Open https://www.kaggle.com/code/{KERNEL} in a browser, "
        "wait for it to finish loading, then click 'Run All' to start the "
        "next chunk."
    )


if __name__ == "__main__":
    main()
