# TripMe Project Rules

## Reproducibility

- Default random seed: `42`.
- Dataset splits must be based on place/group identity, not random rows.
- The same place must not appear in train and hidden-test splits.
- Every training run records model ID, dataset version, seed, commit/version ID and hyperparameters.
- Generated artifacts are never treated as source data.

## Versioning

- Project releases use semantic versions: `MAJOR.MINOR.PATCH`.
- Dataset versions use `vMAJOR.MINOR.PATCH`.
- Increment PATCH for corrections that do not change the schema.
- Increment MINOR when records, scenarios or optional fields are added.
- Increment MAJOR when schemas or compatibility change.
- Adapter names follow `tripme-si-<base>-data-<version>-run-<number>`.

## Data boundaries

- `data/raw/` is read-only source material.
- Cleaned canonical data belongs in `data/processed/`.
- Model-ready splits belong in `data/training/`.
- Reports belong in `reports/`; model/checkpoint outputs belong in `artifacts/`.
- Secrets belong only in ignored `.env` files or platform secret stores.
- Prices, opening hours and current safety information must be retrieved from a dated source rather
  than memorized as timeless facts.

## Completion rule

A roadmap task is complete only when its expected files exist, its validation command passes and
remaining limitations are recorded. A training loss decrease alone does not prove model quality.

