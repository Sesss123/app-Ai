# TripMe Git history notes

This repository keeps source code, configuration, notebooks, compact registry data and project
documentation in Git. Generated model weights, Kaggle inputs/results, reports, review workbooks,
training datasets, virtual environments and secrets stay outside Git.

## Development sequence

1. Project foundation and reproducibility rules.
2. Data audit, cleaning, canonical place IDs and registry creation.
3. Provisional gold-evaluation scaffolding and leakage-safe splits.
4. Pilot, smoke and corrective QLoRA training workflows.
5. Repeat evaluation, automatic release gates and human-review tooling.
6. Candidate model packaging with explicit non-production status.
7. Local place RAG, current-information safeguards and FastAPI backend.
8. Browser test UI and retrieval-quality fixes.
9. Next: advisor schemas, planning/tool datasets and advisor-model training.

## Files intentionally excluded

- `.env` and credentials
- `.venv/` and `node_modules/`
- `kaggle_upload/` and `kaggle_results/`
- `artifacts/` model adapters and release ZIP files
- generated `reports/` and review workbooks
- generated pilot/corrective training datasets

The excluded artifacts can be reproduced with the checked-in scripts and notebooks, except external
Kaggle training outputs, which must be restored separately when required.
