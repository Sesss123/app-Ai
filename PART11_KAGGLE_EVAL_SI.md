# Part 11 — දෙවන Corrective Adapter Evaluation

Part 10 adapter එක Part 6 සහ Part 8 සඳහා භාවිත කළ එකම seed-42 evaluation sample
එක මත නැවත පරීක්ෂා කරයි. එම නිසා metric වෙනස්කම් සාධාරණව සැසඳිය හැක.

Kaggle Dataset එකක් ලෙස upload කරන්න:

```text
kaggle_upload/tripme-part11-corrective-eval
```

Notebook එක:

```text
notebooks/part11_corrective_gold_eval_kaggle.ipynb
```

Settings:

- GPU: `T4`
- Internet: `On`
- Input: `tripme-part11-corrective-eval`
- `Run All`

Download file:

```text
tripme_part11_eval_output.zip
```

Project එකේ පහත ස්ථානයට දමන්න:

```text
kaggle_results/part11/tripme_part11_eval_output.zip
```

මෙය human-approved gold set එකක් නොවේ. Metric gate pass වුවත් production release එකට
වෙනම human review අවශ්‍යය.
