# Kaggle Notebook → Project Folder Workflow

සෑම roadmap part එකකටම මෙම pattern එක භාවිතා කරමු:

```text
Local project data
  -> prepare script
  -> Kaggle Dataset upload
  -> Part notebook Run All
  -> output ZIP download
  -> project/kaggle_results/partXX/
  -> import/validation script
  -> next part
```

## Part 2 සඳහා steps

### 1. Kaggle input එක local machine එකේ සකස් කරන්න

```powershell
python scripts/prepare_part02_kaggle_data.py
```

Upload කළ යුතු folder එක:

```text
kaggle_upload/tripme-part02-data/
```

### 2. Kaggle Dataset එකක් හදන්න

Folder එක private Kaggle Dataset එකක් ලෙස upload කරන්න. Dataset name එක
`tripme-part02-data` ලෙස තැබිය හැක.

### 3. Notebook එක run කරන්න

`notebooks/part02_data_audit_kaggle.ipynb` Kaggle වෙත import කර dataset එක attach කරන්න.
මෙම part එකට GPU අවශ්‍ය නැත. **Run All** කරන්න.

### 4. Output එක download කරන්න

Notebook Output වලින් පහත file එක download කරන්න:

```text
tripme_part02_output.zip
```

### 5. ZIP එක project එකට දාන්න

ZIP file එක මෙතැන තබන්න:

```text
kaggle_results/part02/tripme_part02_output.zip
```

### 6. Output එක validate/import කරන්න

```powershell
python scripts/import_part02_output.py
```

Valid නම් extracted reports මෙතැන ලැබේ:

```text
reports/part02/
```

ඉන්පසු Part 2 manual-review/cleaning tasks ආරම්භ කළ හැක.

## Part 2 cleaning stage

Audit output import කළ පසු cleaning input එක සකස් කරන්න:

```powershell
python scripts/prepare_part02_cleaning_kaggle_data.py
```

`kaggle_upload/tripme-part02-cleaning/` folder එක private Kaggle Dataset එකක් ලෙස upload
කරන්න. `notebooks/part02_cleaning_kaggle.ipynb` import කර එම dataset එක attach කර **Run All**
කරන්න. GPU අවශ්‍ය නැත.

Notebook output එකෙන් `tripme_part02_cleaning_output.zip` download කර මෙතැන තබන්න:

```text
kaggle_results/part02_cleaning/tripme_part02_cleaning_output.zip
```

ඉන්පසු:

```powershell
python scripts/import_part02_cleaning_output.py
```
