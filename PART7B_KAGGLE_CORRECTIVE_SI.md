# Part 7B — Corrective QLoRA Retraining

## 1. Dataset upload

මෙම folder එක private Kaggle Dataset එකක් ලෙස upload කරන්න:

```text
kaggle_upload/tripme-part07b-corrective-train/
```

Dataset name:

```text
tripme-part07b-corrective-train
```

## 2. Notebook import

```text
notebooks/part07b_corrective_train_kaggle.ipynb
```

Settings:

- Accelerator: GPU T4 හෝ T4 x2
- Internet: On
- Input: `tripme-part07b-corrective-train`

`Run All` කරන්න. Notebook එක පරණ adapter එක continue නොකර `Qwen/Qwen2.5-3B-Instruct` base model එකෙන් නැවත train කරයි.

Configuration:

- Train: 1,800
- Validation: 250
- Epochs: 1
- Learning rate: `7e-5`
- LoRA dropout: `0.08`
- Targeted Sinhala generation checks: 20
- Generation limit: 384 tokens

## 3. Output download

```text
tripme_part07b_corrective_output.zip
```

Direct link එක ක්‍රියා නොකරන්නේ නම් `/kaggle/working` refresh කර Output panel එකෙන් download කරන්න.

## 4. Project import

ZIP එක මෙතැනට දමන්න:

```text
kaggle_results/part07b/tripme_part07b_corrective_output.zip
```

ඉන්පසු:

```powershell
python scripts/import_part07b_output.py
```
