# Part 5 — Kaggle QLoRA Smoke Test

## 1. Input Dataset upload

මේ folder එක private Kaggle Dataset එකක් ලෙස upload කරන්න:

```text
kaggle_upload/tripme-part05-smoke/
```

Dataset name: `tripme-part05-smoke`

## 2. Notebook import

Kaggle වෙත මෙය import කරන්න:

```text
notebooks/part05_smoke_train_kaggle.ipynb
```

Settings:

- Accelerator: GPU T4 හෝ T4 x2. Notebook එක QLoRA compatibility සඳහා පළමු T4 GPU එක පමණක්
  visible කරයි; Trainer `DataParallel` භාවිත නොකරයි.
- Internet: On
- Input: `tripme-part05-smoke`

`Run All` කරන්න. Notebook එක examples 200ක් train කර validation examples 40ක් evaluate කරයි.

## 3. Output download

Notebook Output වලින් download කරන්න:

```text
tripme_part05_smoke_output.zip
```

Project එකේ මෙතැන තබන්න:

```text
kaggle_results/part05/tripme_part05_smoke_output.zip
```

## 4. Import

```powershell
python scripts/import_part05_output.py
```

මෙම run එක pipeline smoke test එකක් පමණි. Dataset එක තවම AI draft status එකේ ඇති නිසා resulting
adapter එක production/final model එකක් ලෙස release නොකළ යුතුය.
