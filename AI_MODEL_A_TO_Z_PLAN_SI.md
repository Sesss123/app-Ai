# TripMe Sinhala Travel AI — A සිට Z දක්වා Training Plan

## අවසාන ඉලක්කය

ශ්‍රී ලංකාවේ සංචාරක ස්ථාන ගැන Sinhala, Singlish සහ English භාවිතයෙන් කතා කළ හැකි,
නොදන්නා facts අනුමාන නොකරන, current information සඳහා RAG භාවිතා කරන assistant එකක්
නිර්මාණය කිරීම.

මෙය model එකක් zero සිට pretrain කරන project එකක් නොවේ. දැනට තිබෙන open instruct model
එකකට QLoRA adapter එකක් train කර travel data retrieval system එකක් සම්බන්ධ කරයි.

## Phase A — Accounts සහ tools

අවශ්‍ය නොමිලේ accounts:

1. Kaggle account — notebook සහ GPU සඳහා.
2. Hugging Face account — අවසානයේ adapter/model files තැබීමට. මුල් Qwen run එකට token
   එකක් අනිවාර්ය නොවේ.
3. GitHub account — code සහ version history සඳහා (optional නමුත් නිර්දේශිතයි).

Kaggle premium account එකක් අවශ්‍ය නැත. Free GPU availability සහ quota වෙනස් විය හැකි
නිසා training එක නැවත ආරම්භ කළ හැකි chunks/checkpoints ලෙස සැලසුම් කළ යුතුය.

## Phase B — Problem scope එක lock කිරීම

Version 1 හි assistant එකට අවශ්‍ය හැකියාවන්:

- District/category අනුව places යෝජනා කිරීම.
- Budget, family, accessibility සහ activity constraints සැලකීම.
- කෙටි day plans සහ multi-day itineraries ලිවීම.
- Sinhala, Singlish සහ English prompts තේරුම් ගැනීම.
- නොදන්නා හෝ current facts ගැන පැහැදිලි uncertainty එකක් දැක්වීම.

Version 1ට ඇතුළත් නොකරන දේ:

- Live hotel/flight booking.
- Real-time weather හෝ road conditions model weights තුළ තැබීම.
- Medical, legal හෝ relationship advice.
- Verified source එකක් නැති safety guarantees.

Deliverable: එක පිටුවක product specification සහ expected/forbidden behavior list එක.

## Phase C — Raw data audit සහ cleanup

දැනට raw files 363ක් සහ place records ආසන්න වශයෙන් 7,824ක් ඇත.

ක්‍රියාමාර්ග:

1. `python scripts/00_audit_raw.py` run කිරීම.
2. Invalid/missing coordinates manual-review list එකකට දැමීම.
3. Duplicate IDs සහ duplicate `name + district` records merge/review කිරීම.
4. Generic names (`Temple`, `Church` වැනි) training වලින් තාවකාලිකව ඉවත් කිරීම.
5. එක් record එකකට source, license, source date සහ verification status එකක් එක් කිරීම.
6. Prices, opening times සහ current safety claims static training answers වලින් ඉවත් කිරීම.

Exit condition: training සඳහා භාවිත කරන සෑම fact එකකටම source/provenance එකක් තිබීම.

## Phase D — Evaluation set එක මුලින්ම හදීම

Training කිරීමට පෙර model එක මැනීමට නොපෙනෙන test set එකක් අවශ්‍යයි.

- Human-written prompts: 300
- Sinhala: 150
- Singlish/code-switching: 75
- English: 75
- Place discovery, budget, itinerary, accessibility, uncertainty සහ false-premise prompts ඇතුළත් කරන්න.
- Train/validation data සමඟ එකම place/group එක overlap නොවිය යුතුය.

එක් response එකකට score:

- Sinhala naturalness `/5`
- Factual correctness `/5`
- User constraints follow කිරීම `/5`
- Unsupported claims ගණන
- Useful answer ද නැද්ද

Exit condition: `gold_test.jsonl` freeze කර training generator එකෙන් එය access කළ නොහැකි වීම.

## Phase E — Dataset quality වැඩි කිරීම

දැනට Sinhala training examples 28,775ක් සහ validation examples 3,214ක් ඇත. Quantity එක
පමණක් ප්‍රමාණවත් නොවේ; template repetition අඩු කළ යුතුය.

1. Exact duplicates remove කරන්න.
2. Near-duplicate prompt/answer patterns detect කරන්න.
3. Unsupported “දැන් safe/open” claims remove කරන්න.
4. Human-reviewed natural Sinhala examples අවම වශයෙන් 500ක් මුල් pilot එකට හදන්න.
5. Formal Sinhala, spoken Sinhala, Singlish සහ common typing errors balance කරන්න.
6. Random-row split වෙනුවට place/group split භාවිතා කරන්න.
7. Final target එක human-reviewed examples 4,000–8,000ක් කරගන්න.

Exit condition: automated validation pass වීම සහ random examples 100ක් manual review කිරීම.

## Phase F — Base model benchmark

මුලින් fine-tuning නොකර base model එක gold prompts මත test කරන්න.

මුල් candidate:

- `Qwen/Qwen2.5-3B-Instruct` — open access සහ free GPU smoke test සඳහා පහසුයි.

පසුව A/B test:

- 4B පන්තියේ වෙනත් instruct model එකක්.
- Sinhala fluency, factuality, latency සහ GPU memory මත model එක තෝරන්න.

Exit condition: base scores සහ sample outputs save කර තිබීම.

## Phase G — Kaggle smoke test

භාවිත කළ යුතු notebook: `notebooks/finetune_kaggle.ipynb`

Settings:

- Kaggle free GPU
- `SMOKE_TEST = True`
- Train examples: 200
- Validation examples: 40
- Epoch: 1
- 4-bit NF4 QLoRA
- LoRA rank: 16
- Sequence length: 1,024

පරීක්ෂා කළ යුතු දේ:

- Dataset load වෙනවාද?
- Model 4-bit ලෙස load වෙනවාද?
- CUDA out-of-memory error නැද්ද?
- Training loss අඩුවෙනවාද?
- Adapter files `/kaggle/working/tripme-adapter` තුළ save වෙනවාද?
- Sinhala prompt එකකට readable answer එකක් ලැබෙනවාද?

Failure වුණොත් මුලින් sequence length 768/512ට අඩු කරන්න. පසුව LoRA target modules හෝ
model size අඩු කරන්න.

## Phase H — Gold pilot training

Smoke test pass වූ පසු full generated dataset එකට යාමට පෙර reviewed examples 500–1,000ක්
මත pilot එකක් run කරන්න.

Recommended initial settings:

- Epochs: 1–2
- Learning rate: `1e-4`
- Effective batch size: 8–16
- Sequence length: 1,024
- Evaluation/checkpoint: සෑම 100–250 stepsකටම
- Best checkpoint: validation loss පමණක් නොව gold evaluation scores මත තෝරන්න.

Base model සහ pilot adapter දෙකම එකම gold prompts මත compare කරන්න. Improvement එකක් නැත්නම්
full training නොකර dataset errors හදන්න.

## Phase I — Free-session full training

Full dataset එක එක session එකක අවසන් කිරීමට බලාපොරොත්තු නොවන්න.

1. Dataset එක deterministic shards/chunks වලට බෙදන්න.
2. එක් Kaggle session එකකට fit වන steps/chunk එක පමණක් train කරන්න.
3. Adapter, optimizer state, scheduler state සහ current chunk number output ලෙස save කරන්න.
4. Kaggle notebook version/commit එක අවසන් වූ පසු checkpoint එක private Kaggle Dataset එකකට
   update කරන්න.
5. ඊළඟ session එකේ latest checkpoint එකෙන් resume කරන්න.
6. සෑම chunk එකකට පසුව evaluation run කර regression තිබේද බලන්න.

වැදගත්: වෙන වෙනම model pieces train කර පසුව එකතු නොකරන්න. එක continuous adapter training
run එකක් checkpoints මඟින් resume කරන්න.

## Phase J — Final evaluation

Base model, pilot model සහ final model blind evaluation එකක compare කරන්න.

Release targets:

- Base modelට වඩා pairwise win rate `>60%`
- Unsupported current/safety claims `<1%`
- Sinhala naturalness average `>=4/5`
- Constraint satisfaction average `>=4/5`
- Train/test place leakage `0`

Target pass නොවුණොත් වැඩිපුර epochs දීම වෙනුවට error categories අනුව data හදන්න.

## Phase K — RAG knowledge system

Fine-tuning model එකේ කාර්යය tone, language සහ response behavior ඉගෙනීමයි. Place facts ලබාදීම
RAG system එකේ කාර්යයයි.

Pipeline:

```text
User question
  -> language/intent detection
  -> verified place database search
  -> relevant records + source dates
  -> fine-tuned model
  -> grounded answer + sources/freshness warning
```

RAG database එකේ තැබිය යුතු දේ:

- Place name, district, category සහ coordinates
- Verified description සහ activities
- Source URL සහ verified date
- Opening hours, prices, weather සහ alerts වැනි update විය හැකි fields

## Phase L — Deployment

මුල් deployment එක සඳහා:

1. Base model + LoRA adapter load කරන inference service එකක්.
2. Place retrieval API එකක්.
3. Sinhala/Singlish chat UI එකක්.
4. Request logging තුළ personal data නොතබන privacy rules.
5. Answer එකේ source date සහ uncertainty පෙන්වීම.

Free/low-cost prototype එක CPU මත මන්දගාමී විය හැක. Quantized inference හෝ on-demand GPU
භාවිතා කළ හැක. Production hosting cost එක training cost එකෙන් වෙනම සැලසුම් කළ යුතුය.

## Phase M — Release සහ monitoring

- Adapter, tokenizer config, model card සහ data card publish කරන්න.
- Base model license සහ dataset licenses verify කරන්න.
- User feedback සඳහා thumbs-up/down සහ issue category ලබාදෙන්න.
- Wrong-place, stale-info, unsafe-claim සහ language-quality errors වෙන වෙනම track කරන්න.
- Verified data update කර RAG index refresh කරන්න; සෑම data update එකකටම model retrain නොකරන්න.

## ක්‍රියාත්මක කිරීමේ අනුපිළිවෙළ

1. Scope freeze
2. Raw data audit/verification
3. 300-prompt gold test set
4. Dataset cleanup සහ 500 reviewed examples
5. Base model benchmark
6. Kaggle 200-example smoke test
7. 500–1,000 example pilot
8. Pilot evaluation සහ error fixing
9. Checkpoint-resumable full QLoRA run
10. Blind final evaluation
11. RAG integration
12. API/UI deployment
13. Monitoring සහ periodic data updates

## දැන්ම කළ යුතු ඊළඟ task එක

Training run කිරීම නොව, දැනට තිබෙන Sinhala dataset එකෙන් unsafe/current factual claims සහ
duplicate templates සොයා quality report එකක් නිර්මාණය කිරීම. ඒ report එක මත clean pilot dataset
එක හදලා පසුව Kaggle smoke test එක run කළ යුතුය.
