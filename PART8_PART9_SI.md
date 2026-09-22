# Part 8 සහ Part 9

## Part 8 — Corrective adapter re-evaluation

Kaggle Dataset ලෙස upload කරන්න:

```text
kaggle_upload/tripme-part08-corrective-eval/
```

Notebook:

```text
notebooks/part08_corrective_gold_eval_kaggle.ipynb
```

Settings: GPU T4, Internet On, Input `tripme-part08-corrective-eval`, ඉන්පසු `Run All`.

Download:

```text
tripme_part08_eval_output.zip
```

Project path:

```text
kaggle_results/part08/tripme_part08_eval_output.zip
```

Import:

```powershell
python scripts/import_part08_output.py
```

## Part 9 — Release gate

Part 8 import කළ පසු:

```powershell
python scripts/run_part09_release_gate.py
```

Metric gate pass වුවත් human approval file එකක් නැතිනම් release එක block වේ. Human reviewer විසින් review queue එක පරීක්ෂා කළ පසු පමණක් `reports/part09/human_approval.json` තුළ reviewer සහ `status: approved` සටහන් කළ යුතුය. AI විසින් එම approval එක නිර්මාණය නොකළ යුතුය.
