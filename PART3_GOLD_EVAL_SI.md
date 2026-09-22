# Part 3 — Gold Evaluation Set

## අරමුණ

Model training එකෙන් ස්වාධීනව model quality මැනීමට prompts 500ක hidden human-gold test set
එකක් සහ prompts 10,000ක automated coverage set එකක් සෑදීම.
Gold set එක model training, prompt generation හෝ hyperparameter selection සඳහා භාවිතා නොකළ යුතුය.

## Distribution

- Sinhala: 250
- Singlish/code-switching: 125
- English: 125
- Total: 500

Scenario counts `config/gold_eval_spec.json` තුළ lock කර ඇත.

## Files

- `gold_authoring_sheet.csv` — human authors/reviewers පිරවිය යුතු sheet එක.
- `gold_scaffold.jsonl` — machine-readable blank scaffold එක.
- `holdout_places.jsonl` — evaluation සඳහා වෙන් කළ complete place context.
- `holdout_place_ids.txt` — Part 4 training dataset එකෙන් අනිවාර්යයෙන් ඉවත් කළ යුතු IDs.
- `scaffold_summary.json` — distribution summary.

## Human authoring rules

1. Prompt එක author කෙනෙකු විසින් natural language එකෙන් ලියන්න.
2. Reference answer එක supplied holdout context පමණක් භාවිතයෙන් ලියන්න.
3. Current prices, hours, weather හෝ safety facts verify කර නැත්නම් answer එක uncertainty පෙන්විය යුතුය.
4. Author සහ reviewer එකම පුද්ගලයා නොවිය යුතුය.
5. Reviewer factuality, naturalness සහ forbidden claims පරීක්ෂා කර `approved` කළ යුතුය.
6. Gold prompts/answers training JSONL files වෙත copy නොකරන්න.

## Validation

Scaffold validation:

```powershell
python scripts/validate_gold_eval.py --mode scaffold
```

Human review අවසන් වූ final file එක validate කිරීම:

```powershell
python scripts/validate_gold_eval.py --path <final-jsonl-path> --mode final
```

## Current state

Part 3 scaffold එක machine-generated assignment plan එකක් පමණි. Blank prompts සහ reference answers
human authors/reviewers විසින් සම්පූර්ණ කරන තුරු එය gold evaluation set එකක් නොවේ.

## Part 3B automated coverage set

- Total prompts: 10,000
- Sinhala: 5,000
- Singlish: 2,500
- English: 2,500
- Covered primary places: 4,473
- Input: OSM-attributed Part 2 subset only

Files:

- `data/evaluation/coverage_v0.1.0/coverage_eval_10000.jsonl`
- `data/evaluation/coverage_v0.1.0/coverage_summary.json`
- `config/coverage_eval_spec.json`

Validation:

```powershell
python scripts/validate_coverage_eval.py
```

මෙම set එක automatic grounding/coverage checks සඳහාය. එය human gold set එකක් නොවේ.
