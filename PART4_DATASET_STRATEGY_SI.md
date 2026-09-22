# Part 4 — Training Dataset Strategy

## Legacy generated dataset decision

Existing Sinhala candidate rows leakage සහ source rules අනුව filter කළ පසු 543 rows ලැබුණත්,
unique prompt-template signatures 8ක් පමණක් ඇත. එම dataset එක training සඳහා reject කර ඇත.

`data/training/pilot_v0.1.0/DO_NOT_TRAIN.json` තිබෙන dataset එක කිසිදු training notebook එකකට
input ලෙස attach නොකළ යුතුය.

## Replacement pilot target

අලුත් pilot dataset එක:

- Total examples: 800–1,000
- Sinhala: 70%
- Singlish/code-switching: 20%
- English: 10%
- Unique structural prompt ratio: අවම 20%
- Gold holdout overlap: 0
- Train/validation place overlap: 0
- Source-attributed registry places only
- Unsupported current-price/opening/safety claims: 0

## Scenario balance

- Discovery/recommendation: 20%
- Place explanation: 15%
- Comparison: 10%
- Itinerary/planning: 20%
- Family/accessibility: 10%
- Budget with uncertainty: 10%
- Current-fact refusal/clarification: 10%
- Cultural etiquette: 5%

## Approval rule

Generated drafts are not training-approved automatically. Automated checks must pass, followed by
language/factual review of every pilot example or a documented statistically valid review process.
