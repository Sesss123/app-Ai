# TripMe Sinhala AI — Kaggle training ආරම්භය

මුල් පියවරේ අරමුණ model එක සම්පූර්ණයෙන් train කිරීම නොව, examples 200ක් යොදාගෙන
pipeline එක නිවැරදිව ක්‍රියාකරන බව තහවුරු කිරීමයි.

## 1. Kaggle data folder එක සකස් කිරීම

Project root එකේදී:

```powershell
python scripts/prepare_kaggle_data.py
```

එවිට `kaggle_upload/tripme-data/` තුළ පහත files ලැබේ:

- `train_si.jsonl`
- `val_si.jsonl`
- `dataset-metadata.json`
- `data-summary.json`

`dataset-metadata.json` තුළ `YOUR_KAGGLE_USERNAME` වෙනුවට ඔබගේ Kaggle username එක
යොදන්න. පසුව Kaggle CLI භාවිතයෙන් upload කළ හැක:

```powershell
kaggle datasets create -p kaggle_upload/tripme-data
```

නැතිනම් Kaggle website එකෙන් **New Dataset** තෝරා files දෙක upload කරන්න.

## 2. Kaggle Notebook එක සකස් කිරීම

1. Kaggle හි **New Notebook** තෝරන්න.
2. Accelerator ලෙස **GPU T4 x2** හෝ **GPU T4** තෝරන්න.
3. Internet `On` කරන්න.
4. Input ලෙස private `tripme-data` dataset එක add කරන්න.
5. `notebooks/finetune_kaggle.ipynb` upload/import කරන්න.
6. Notebook එකේ `MODEL_ID` සහ `DATA_DIR` cells පරීක්ෂා කරන්න.
7. මුල් වරට `SMOKE_TEST = True` තබා **Run All** කරන්න.

## 3. Hugging Face access

Notebook එක default ලෙස `Qwen/Qwen2.5-3B-Instruct` භාවිතා කරන නිසා gated-model
approval එකක් හෝ token එකක් අවශ්‍ය නොවේ. පසුව Gemma model එකකට මාරු වන්නේ නම් Kaggle
Secrets තුළ `HF_TOKEN` එක තබා model license එක accept කළ යුතුය.

## 4. සාර්ථක run එකක ලැබිය යුතු output

`/kaggle/working/tripme-adapter/` තුළ LoRA adapter සහ tokenizer files save වේ.
Notebook අවසානයේ Sinhala test prompt එකකට base model එකෙන් සහ trained adapter එකෙන්
ලැබෙන response එක පෙන්වයි.

Smoke test එක සාර්ථක වූ පසු:

```python
SMOKE_TEST = False
```

කර full dataset run එකක් ආරම්භ කළ හැක. Full run එකට පෙර dataset quality review කිරීම
නිර්දේශ කෙරේ; දැනට generated examples අතර unsupported safety/current-fact claims තිබිය හැක.
