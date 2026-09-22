# Part 6 — Provisional Gold Evaluation

## වැදගත් සීමාව

මෙම evaluation references AI drafts වේ. ඒවා human-approved gold labels නොවේ. මෙම run එක diagnostic evaluation එකක් පමණි.

## 1. Kaggle Dataset upload

මෙම folder එක private Kaggle Dataset එකක් ලෙස upload කරන්න:

```text
kaggle_upload/tripme-part06-provisional-eval/
```

Dataset name:

```text
tripme-part06-provisional-eval
```

## 2. Notebook import

```text
notebooks/part06_provisional_gold_eval_kaggle.ipynb
```

Settings:

- Accelerator: GPU T4 හෝ T4 x2
- Internet: On
- Input: `tripme-part06-provisional-eval`

`Run All` කරන්න. Notebook එක adapter prompts 120ක් සහ base-model comparison prompts 30ක් generate කරයි. Sinhala answers මැදින් කැපීම වැළැක්වීමට `max_new_tokens=384` භාවිතා කරයි.

## 3. Output download

```text
tripme_part06_eval_output.zip
```

Direct link එක ක්‍රියා නොකරන්නේ නම් `/kaggle/working` refresh කර Output panel menu එකෙන් download කරන්න.

## 4. Project import

ZIP එක මෙතැනට දමන්න:

```text
kaggle_results/part06/tripme_part06_eval_output.zip
```

ඉන්පසු:

```powershell
python scripts/import_part06_output.py
```
