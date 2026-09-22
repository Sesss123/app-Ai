# TripMe AI — වැඩ කිරීමට පහසු Roadmap Parts

මුළු project එක ප්‍රධාන parts 8කට බෙදා ඇත. එක part එක අවසන් කර verify කළ පසුව පමණක්
ඊළඟ part එකට යන්න.

## Part 1 — Project foundation

### අරමුණ

AI assistant එක කළ යුතු දේ සහ project files පිළිවෙළට සකස් කිරීම.

### Tasks

- Version 1 product scope එක approve කිරීම.
- Supported languages සහ features lock කිරීම.
- Out-of-scope features lock කිරීම.
- Folder structure සහ configuration files සකස් කිරීම.
- Python dependencies list එකක් සෑදීම.
- Reproducible random seed සහ version naming rules තීරණය කිරීම.

### ලැබෙන output

- `PRODUCT_SCOPE_SI.md`
- Project configuration
- Requirements/dependencies file

### Part එක අවසන් වන්නේ

Version 1ට feature එකක් ඇතුළත්ද නැද්ද කියා document එකෙන් පැහැදිලිව තීරණය කළ හැකි විට.

---

## Part 2 — Data audit සහ cleaning

### අරමුණ

Raw place data training සහ retrieval සඳහා විශ්වාසදායක තත්ත්වයකට ගෙන ඒම.

### Tasks

- Raw JSON files parse සහ audit කිරීම.
- Missing fields report කිරීම.
- Invalid coordinates හඳුනාගැනීම.
- Duplicate places හඳුනාගැනීම.
- District/category names normalize කිරීම.
- Source, license සහ verification status එක record කිරීම.
- Current prices, opening hours සහ unsupported safety claims වෙන් කිරීම.

### ලැබෙන output

- Clean place dataset
- Data-quality report
- Manual-review queue
- Rejected-records file

### Part එක අවසන් වන්නේ

Clean dataset එකේ සෑම accepted record එකක්ම validation rules pass කරන විට.

---

## Part 3 — Gold evaluation set

### අරමුණ

Training කළ model එක ඇත්තටම හොඳ වුණාද කියා මැනීමට independent test set එකක් සෑදීම.

### Tasks

- Evaluation schema එක තීරණය කිරීම.
- Human-written prompts 300ක් සකස් කිරීම.
- Sinhala prompts 150ක් සකස් කිරීම.
- Singlish/code-switch prompts 75ක් සකස් කිරීම.
- English prompts 75ක් සකස් කිරීම.
- Correct facts, expected behavior සහ scoring rubric එක එක් කිරීම.
- Training data සමඟ place/prompt leakage පරීක්ෂා කිරීම.

### ලැබෙන output

- Hidden `gold_test.jsonl`
- Human scoring sheet
- Automatic evaluation script

### Part එක අවසන් වන්නේ

Gold test set එක freeze කර training pipeline එකෙන් වෙන් කර තැබූ විට.

---

## Part 4 — Training dataset preparation

### අරමුණ

Natural, safe සහ model training සඳහා සුදුසු conversation dataset එකක් සෑදීම.

### Tasks

- Exact duplicates ඉවත් කිරීම.
- Near-duplicate templates හඳුනාගැනීම.
- Unsupported current/safety claims ඉවත් කිරීම.
- Bad Sinhala/encoding issues සොයා නිවැරදි කිරීම.
- Human-reviewed pilot examples 500–1,000ක් සකස් කිරීම.
- Sinhala, Singlish, code-switching සහ English balance කිරීම.
- Place/group-based train-validation split එකක් සෑදීම.

### ලැබෙන output

- `pilot_train.jsonl`
- `pilot_val.jsonl`
- Dataset statistics සහ quality report

### Part එක අවසන් වන්නේ

Automated validation pass වී random examples 100ක් human review කර accept කළ විට.

---

## Part 5 — Model training

### අරමුණ

Free Kaggle GPU එක භාවිතයෙන් QLoRA adapter එක train කිරීම.

### Tasks

- Fine-tuning නොකළ base model එක benchmark කිරීම.
- Examples 200ක smoke test එක run කිරීම.
- Memory, loss සහ checkpoint saving පරීක්ෂා කිරීම.
- Reviewed examples 500–1,000ක pilot training run කිරීම.
- Pilot model එක gold test set එකෙන් evaluate කිරීම.
- Improvement තිබේ නම් full dataset එක chunks වලින් train කිරීම.
- සෑම session එකකටම checkpoint save/resume කිරීම.

### ලැබෙන output

- Base-model benchmark report
- Smoke-test adapter
- Pilot adapter
- Final QLoRA adapter
- Training logs සහ checkpoints

### Part එක අවසන් වන්නේ

Final adapter එක gold evaluation targets pass කර reproducibly load කළ හැකි විට.

---

## Part 6 — RAG සහ knowledge database

### අරමුණ

Model එක facts නිර්මාණය නොකර verified place information මත පිළිතුරු දෙන පද්ධතියක් සෑදීම.

### Tasks

- Clean place records search/index format එකකට මාරු කිරීම.
- User query එකෙන් district, category සහ constraints හඳුනාගැනීම.
- Relevant places retrieve කිරීම.
- Retrieved context model prompt එකට එක් කිරීම.
- Source URL සහ verification date answer එක සමඟ ලබාදීම.
- No-result සහ conflicting-data behavior implement කිරීම.
- Prompt-injection resistance test කිරීම.

### ලැබෙන output

- Searchable place database/index
- Retrieval module
- Grounded prompt builder
- RAG evaluation report

### Part එක අවසන් වන්නේ

Assistant responses retrieved records මත පදනම් වන බව automated tests මඟින් තහවුරු වූ විට.

---

## Part 7 — Application සහ deployment

### අරමුණ

Model සහ RAG system එක සාමාන්‍ය user කෙනෙකුට භාවිත කළ හැකි application එකක් කිරීම.

### Tasks

- Chat API එක සෑදීම.
- Model + adapter loading service එක සෑදීම.
- RAG retrieval එක API එකට සම්බන්ධ කිරීම.
- Mobile-friendly Sinhala chat UI එක සෑදීම.
- Loading, error සහ no-result states සෑදීම.
- Rate limiting සහ basic privacy controls එක් කිරීම.
- Development deployment එකක් සකස් කිරීම.

### ලැබෙන output

- Working backend API
- Working chat interface
- Deployment configuration

### Part එක අවසන් වන්නේ

User කෙනෙකුට browser එකෙන් question එකක් අසා grounded answer එකක් ලබාගත හැකි විට.

---

## Part 8 — Testing, release සහ maintenance

### අරමුණ

System එක release කිරීමට පෙර quality, safety සහ reliability තහවුරු කිරීම.

### Tasks

- End-to-end functional testing.
- Native Sinhala reviewer evaluation.
- Unsafe/stale information red-team testing.
- Wrong district සහ false-premise testing.
- Model card, data card සහ limitations ලිවීම.
- Feedback සහ error tracking එක් කිරීම.
- RAG data update schedule එකක් තීරණය කිරීම.
- Version 1 release කිරීම.

### ලැබෙන output

- Final evaluation report
- Release-ready application
- Model/data documentation
- Maintenance checklist

### Part එක අවසන් වන්නේ

Release targets pass වී known limitations userට පැහැදිලිව පෙන්වන production version එකක් තිබෙන විට.

---

## සරල project flow එක

```text
Part 1: Scope
   ↓
Part 2: Clean data
   ↓
Part 3: Gold test set
   ↓
Part 4: Training dataset
   ↓
Part 5: Train model
   ↓
Part 6: Add RAG
   ↓
Part 7: Build application
   ↓
Part 8: Test and release
```

## වැඩ කිරීමේ නීතිය

- එක් අවස්ථාවක active කරන්නේ එක part එකක් පමණි.
- එක් part එක තුළත් එක task එක බැගින් complete කරන්න.
- Output එක validate නොකර ඊළඟ task එකට නොයන්න.
- Training ඉක්මනින් පටන්ගැනීම සඳහා data-quality සහ evaluation parts මඟ නොහරින්න.
- සෑම part එකක් අවසානයේ files, results සහ remaining problems කෙටි report එකක save කරන්න.

## වත්මන් තත්ත්වය

- Part 1: සම්පූර්ණයි. Scope, dependencies, central configuration, versioning rules,
  artifact/report directories සහ foundation validation command එක සකස් කර ඇත.
- Part 2: සම්පූර්ණයි. Raw audit, structural cleaning, strict JSONL conversion, duplicate/coordinate
  quarantine සහ provenance-ready OSM subset එක සකස් කර ඇත. Human fact verification backlog එක
  quarantine/provenance limitations ලෙස explicitly carry forward කර ඇත.
- Part 3: ක්‍රියාත්මකයි. 500-item human-gold scaffold, 710-place hidden holdout සහ 10,000-item
  automated coverage set සකස් කර validate කර ඇත. Gold prompts/reference answers human review කිරීම
  තවම අවසන් නැත; AI-assisted drafts 500ම සකස් කර ඇත; automated Part 3B කොටස සම්පූර්ණයි.
- Part 4: ක්‍රියාත්මකයි. Legacy template-heavy pilot එක reject කර, source-attributed places 1,500ක්
  භාවිත කරන 1,000-item multilingual replacement draft එක සකස් කර automated quality gate pass කර ඇත.
  Human quality review සහ final approval pending.
- Part 5: smoke stage සම්පූර්ණයි. 200-train/40-validation completion-only QLoRA run එක Kaggle T4
  මත pass වී adapter, metrics සහ step-25 checkpoint validate/import කර ඇත. Full 1,000-example
  pilot run සහ human-reviewed dataset approval pending.
- Parts 6–8: ආරම්භ කර නැත.

Part 1 validation command:

```powershell
python scripts/check_foundation.py
```

දැන් කළ යුතු task එක: Part 3 සඳහා gold evaluation-set schema සහ category distribution සකස් කිරීම.
