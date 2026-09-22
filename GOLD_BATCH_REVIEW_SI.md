# Gold Batch Human Review Guide

## Current batch

- IDs: `gold-001` සිට `gold-050`
- JSONL: `data/evaluation/gold_v0.1.0/gold_batch_001_050_draft.jsonl`
- Spreadsheet: `data/evaluation/gold_v0.1.0/gold_batch_001_050_draft.csv`
- Status: AI-assisted draft; gold ලෙස භාවිතයට තවම අනුමත නැත.

## Review කරන ආකාරය

CSV file එක Excel/Google Sheets එකකින් open කර එක් row එකකට:

1. `prompt` natural Sinhala/Singlish/English ද බලන්න; අවශ්‍ය නම් rewrite කරන්න.
2. `reference_answer` supplied facts වලින් පමණක් ලියා තිබේද බලන්න.
3. Current price, opening hours, weather, road හෝ safety claim එකක් invented කර නැද්ද බලන්න.
4. `required_facts` සමඟ answer එක compare කරන්න.
5. Human authorගේ identifier එක `author_id` තුළ දාන්න.
6. වෙනත් reviewer කෙනෙකු review කර `reviewer_id` දාන්න.
7. Accept කළ row එකේ `review_status` value එක `approved` කරන්න.

Author සහ reviewer එකම පුද්ගලයා නොවිය යුතුය. Draft text වෙනස් නොකර approve කිරීම වෙනුවට
language naturalness සහ factual grounding දෙකම සැබෑවට පරීක්ෂා කරන්න.

## Validation

Reviewed CSV එක JSONL බවට import කරන step එක ඊළඟට සකස් කළ යුතුය. Final JSONL එක ලැබුණු පසු:

```powershell
python scripts/validate_gold_eval.py --path <reviewed-batch.jsonl> --mode final
```

