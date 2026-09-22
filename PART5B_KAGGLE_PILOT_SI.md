# Part 5B — Full Pilot QLoRA Training

## 1. Kaggle dataset එක upload කරන්න

මෙම folder එක private Kaggle Dataset එකක් ලෙස upload කරන්න:

```text
kaggle_upload/tripme-part05b-pilot-train/
```

Dataset name:

```text
tripme-part05b-pilot-train
```

මෙහි second-checked train examples 900ක් සහ validation examples 100ක් ඇත.

## 2. Notebook එක import කරන්න

Kaggle notebook එකක් ලෙස මෙය import කරන්න:

```text
notebooks/part05b_pilot_train_kaggle.ipynb
```

Settings:

- Accelerator: GPU T4 හෝ T4 x2
- Internet: On
- Input: `tripme-part05b-pilot-train`

Notebook එක training සඳහා පළමු visible GPU එක පමණක් භාවිතා කරයි. `Run All` කරන්න.

## 3. Training output එක download කරන්න

අවසන් cell එකෙන් මෙම file එක download කරන්න:

```text
tripme_part05b_pilot_output.zip
```

Browser download link එක ක්‍රියා නොකරන්නේ නම් Kaggle දකුණු පස `Output` panel එකේ `/kaggle/working` folder එක expand කර file එකේ menu එකෙන් Download කරන්න. Notebook path එක browser address bar එකට paste නොකරන්න.

## 4. Project එකට දමන්න

Download කළ ZIP එක මෙතැනට දමන්න:

```text
kaggle_results/part05b/tripme_part05b_pilot_output.zip
```

ඉන්පසු:

```powershell
python scripts/import_part05b_output.py
```

මෙම adapter එක production model එකක් නොවේ. Import කිරීමෙන් පසු Part 6 evaluation සහ Sinhala human review sample එක සම්පූර්ණ කළ යුතුය.
