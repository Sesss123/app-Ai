# Part 10 — දෙවන Corrective Training

Part 8 evaluation එකෙන් හඳුනාගත් itinerary place-name loss, family accessibility,
culture/etiquette, current-information සහ encoding වැරදි අඩු කිරීම සඳහා මෙම training
package එක සකස් කර ඇත.

## Kaggle වෙත upload කරන්න

Dataset එකක් ලෙස පහත folder එක upload කරන්න:

```text
kaggle_upload/tripme-part10-corrective-train
```

Notebook එක:

```text
notebooks/part10_corrective_train_kaggle.ipynb
```

Kaggle settings:

- Accelerator: `GPU T4`
- Internet: `On`
- Input dataset: `tripme-part10-corrective-train`
- ඉන්පසු `Run All`

Training අවසානයේ download කළ යුතු file එක:

```text
tripme_part10_corrective_output.zip
```

Download කර project එකේ පහත path එකට දමන්න:

```text
kaggle_results/part10/tripme_part10_corrective_output.zip
```

මෙම dataset එක AI corrective draft එකක් බැවින් final production release සඳහා වෙනම
human review සහ නැවත gold evaluation අවශ්‍යය.
