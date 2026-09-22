# ශ්‍රී ලාංකික සිංහල Travel AI — අඩු වියදම් සැලැස්ම

## මුලින්ම ගන්න තීරණය

මෙය මුල සිට සියලු parameters train කරන foundation model එකක් නොවිය යුතුය. දැනට ඇති open-weight instruction model එකකට **QLoRA adapter fine-tuning + RAG** යොදාගන්න. Colab GPU එකකින් 4B model එකක් full-parameter train කිරීම ප්‍රායෝගික නැත; QLoRA මඟින් train කරන්නේ කුඩා adapter කොටස පමණි.

ආරම්භක base model නිර්දේශය: `google/gemma-3-4b-it`. Sinhala benchmark එකක් කළ පසු `Qwen/Qwen3-4B` සමඟ A/B test කරන්න. Model එක තෝරන්නේ Sinhala fluency, hallucination rate, travel factuality සහ latency යන මිනුම් අනුවය—brand/name එක අනුව නොවේ.

## දැනට data තත්ත්වය

- Raw files 363; place records 7,824.
- `.jsonl` extension තිබුණත් files 363ම strict JSONL නොව pretty-printed consecutive JSON objects වේ.
- ශ්‍රී ලංකා bounding box එකෙන් පිට හෝ verify නොකළ coordinates 164ක් ඇත; තවත් required coordinate values 11ක් missing/zero ලෙස පෙනේ.
- duplicate ID 1ක් සහ duplicate `name + district` candidates 941ක් ඇත.
- Travel Sinhala training examples සுமார் 32,000ක් ඇත. ඒවා template-heavy නිසා එකම වාක්‍ය රටාව නැවත නැවත model එකට ඉගැන්වීමේ අවදානම ඇත.
- Relationship-advice corpus එකක් මේ repository එකේ නොමැත. Travel assistant එකට අදාළ නොවන domain එක එකම adapter එකට දැමීම මුල් release එකට නිර්දේශ නොකරයි.

සම්පූර්ණ machine-readable audit එක `data/processed/raw_audit.json` තුළ නිපදවිය හැක:

```powershell
python scripts/00_audit_raw.py
```

## Phase 1 — Data සත්‍යාපනය

1. Raw files read-only ලෙස තබන්න. `data/verified/` යටතේ canonical copy එකක් හදන්න.
2. එක් place එකකට canonical ID, official/OSM source URL, source date, license, district, category සහ `verified_at` තබන්න.
3. වැරදි coordinates අනුමානයෙන් හදන්න එපා. OSM/official tourism source එකකින් තහවුරු වන තුරු `null` + `coordinate_status="needs_review"` කරන්න.
4. Ticket price, opening hours, safety, road condition සහ weather වැනි වෙනස් වන fields model weights තුළ memorize නොකර RAG database එකට දමන්න.
5. Generic names (`Temple`, `Church`, `Mosque`) සහ duplicate candidates manual review queue එකට දමන්න.
6. Data license/provenance නොමැති generated descriptions training එකෙන් ඉවත් කරන්න හෝ `synthetic=true` ලෙස ලකුණු කරන්න.

## Phase 2 — Sinhala quality dataset

ඉලක්කය examples ගණන වැඩි කිරීම නොව quality වැඩි කිරීමයි.

- Human-reviewed, natural Sri Lankan Sinhala conversations 4,000–8,000ක් මුල් version එකට ප්‍රමාණවත් baseline එකකි.
- Formal Sinhala, everyday spoken Sinhala, Singlish, typo variants සහ Sinhala-English code switching සමබර කරන්න.
- Scenario buckets: place discovery, budget, family, accessibility, route constraints, multi-day plans, food/culture etiquette, uncertainty/refusal, source-date disclosure.
- Static data මත “දැන් safe”, “දැන් open”, “අද price” කියා තහවුරු නොකරන negative examples එක් කරන්න.
- Template එකම paraphrase කර examples දහස් ගණනක් සෑදීම නවත්වන්න. Near-duplicate prompts/answers semantic dedup කරන්න.
- Split කිරීම random row split නොව **place/group split** විය යුතුය: train 80%, validation 10%, hidden test 10%. එකම place එක splits දෙකකට නොයන්න.

## Phase 3 — Model architecture

```text
User (Sinhala/Singlish)
  -> intent + constraints
  -> retrieval (verified places + current facts)
  -> 4B instruct model + QLoRA adapter
  -> citation/freshness + safety checks
  -> answer
```

Fine-tuning එකෙන් tone, Sinhala conversation style, question asking, itinerary formatting සහ grounded refusal ඉගැන්විය යුතුය. Places, prices, opening hours සහ live safety RAG එකෙන් ලබාදිය යුතුය.

## Phase 4 — Colab training recipe

- 4-bit QLoRA (NF4), LoRA rank 16 හෝ 32, gradient checkpointing.
- Sequence length මුලින් 2,048; දිගු itinerary examples සඳහා අවශ්‍ය නම් 4,096.
- Effective batch size 16–32 සඳහා micro-batch 1–2 + gradient accumulation.
- Epochs 1–3; learning rate search `5e-5`, `1e-4`, `2e-4`.
- Completion-only loss භාවිතා කර user/system tokens මත loss නොගන්න.
- Dataset එක token-count අනුව deterministic shards කරන්න (උදා: 25M tokens per shard). **Model parameters කැබලි කර වෙන වෙනම train කිරීම නොකරන්න.** එක් continuous run එකක් checkpoint වලින් resume කරන්න.
- සෑම 200–500 stepsකට checkpoint; Google Drive එකට adapter, optimizer state සහ trainer state save කරන්න. Colab disconnect වුවහොත් latest checkpoint එකෙන් resume කරන්න.
- පළමුව 200-example smoke run; පසුව 10% pilot; metrics pass වුවහොත් full dataset.

## Phase 5 — “හොඳම” බව මිනීම

අනිවාර්ය hidden test set එක native Sinhala reviewers දෙදෙනෙකු හෝ වැඩි දෙනෙකු score කළ යුතුය:

- Sinhala naturalness /5
- factual correctness /5
- retrieved context එකට grounded ද /5
- constraint satisfaction /5
- useful itinerary quality /5
- unsafe/current fact hallucination rate (ඉලක්කය <1%)
- baseline model සමඟ pairwise win rate (ඉලක්කය >60%)

“World No.1” කියන ප්‍රකාශය benchmark සහ independent evaluation නැතිව කරන්න බැහැ. පළමු සාධාරණ ඉලක්කය: **ශ්‍රී ලංකා travel සඳහා verified, citation-aware, Sinhala-first assistant එකක්**.

## Release අනුපිළිවෙළ

1. Raw audit සහ verification queue.
2. 300-example gold evaluation set.
3. Base-model A/B test (fine-tune කිරීමට පෙර).
4. 500–1,000 gold Sinhala examples මත pilot QLoRA.
5. Error analysis; templates සහ false safety claims ඉවත් කිරීම.
6. 4,000–8,000 reviewed examples මත final QLoRA.
7. RAG integration සහ citations.
8. Red-team: wrong district, stale prices, unsafe routes, prompt injection, unsupported claims.
9. Adapter + tokenizer + model card + data card release.

## Relationship advice අවශ්‍ය නම්

එය travel data සමඟ එකවර mix නොකර දෙවන adapter/dataset එකක් ලෙස පවත්වාගෙන යන්න. Crisis/self-harm escalation, abuse/coercive-control safety, privacy සහ “professional help needed” boundaries සඳහා වෙනම expert-reviewed evaluation එකක් අවශ්‍යය. පළමු release එක travel-only තබා success මිනීම පහසු කරගන්න.
