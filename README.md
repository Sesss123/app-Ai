# TripMe AI Mode

Fine-tuned LLM pipeline for TripMe's voice-based, location-aware Sri Lanka place recommendations, in English and Sinhala. See `C:\Users\sehas\.claude\plans\velvet-watching-hamming.md` for the full design doc.

## Status

- [x] Dataset downloaded (6 category JSON files, 1289 places, 25 districts) - `data/raw/`
- [x] Merged, cleaned (district spelling fixed, CJK corruption in 6 descriptions scrubbed) - `data/processed/places.json`
- [x] English instruction dataset generated (5,531 examples: single/family/safety/compare/day-trip/budget-concierge/audio-guide scenarios) - `data/training/{train,val}.jsonl`
- [x] Sinhala instruction dataset generated (5,531 examples, same scenarios, hand-written formal Sinhala grounded in the place data - not machine translation) - `data/training/{train_si,val_si}.jsonl`
- [x] Both datasets validated (0 issues: no empty responses, no contamination, no unknown place IDs, no safety contradictions)
- [x] Colab fine-tuning notebook ready, base model `ihalage/llama3-sinhala` (Llama-3-8B-Instruct already Sinhala-capable), trains on English + Sinhala together - `notebooks/finetune_colab.ipynb`
- [x] Serving API scaffolded and smoke-tested (retrieval + language-aware LLM routing + FastAPI wiring confirmed) - `serve/`
- [ ] **Not done yet**: actually running the fine-tune on Colab, merging/exporting to GGUF, deploying the API, Tamil data + TTS

## Why `ihalage/llama3-sinhala` as the base model

The places dataset has no Sinhala text at all (only English `description` fields), so a generic base model (Phi-3, vanilla Llama-3, Gemma) would need to learn Sinhala from scratch during this fine-tune - unrealistic with ~4k Sinhala examples. `ihalage/llama3-sinhala` is a Llama-3-8B-Instruct model already fine-tuned for Sinhala (Apache 2.0, LoRA rank 16). This project's fine-tune only needs to teach it the TripMe voice and ground it in the Sri Lanka places data - a narrower, more realistic task for this dataset size.

## Budget Concierge scenario

Added as a 6th scenario type (`budget_concierge`) alongside the existing 5. Unlike the other scenarios (which are grounded in real place records), there's no real trip-spending data in the source dataset, so this uses **synthesized but realistic** budget scenarios: total budget, days elapsed/remaining, and a spend breakdown across transport/food/tickets/stay that's randomly skewed toward one category, loosely anchored to a real nearby place's price via `cheapest_nearby`.

Critically, the synthesized numbers are included **in the user turn** (formatted as a context block a real app would provide - total budget, spent so far, category breakdown, days), not just baked into the assistant's answer - the model has to learn to compute its percentages/pace assessment/advice from the given numbers, not invent them. Matches this shape:

```
User: My trip: 3 days in Gampaha, day 1 just finished (2 days left). Total budget: 35000 LKR.
Spent so far: 8000 LKR (transport 1300, food 3900, tickets 1400, stay 1400).

Am I on track with my spending?

Assistant: You're at 23% of your budget with 2 days left, right on pace. Your food spend is
on the high side, at about 49% of what you've spent so far in Gampaha. Consider trying more
local eateries instead of hotel/tourist restaurants for your remaining meals to bring that
down. Negombo Water Sports Park nearby is free to enter if you want a no-cost stop.
```

This is a capability trained into the same fine-tuned model, not a separate model/API call - once trained, the app would pass live trip-budget data (already computed app-side) into the prompt the same way, in place of the synthetic numbers used here.

## Audio Guide scenario

Added as a 7th scenario type (`audio_guide`), for when the user taps a button while standing at a place (not GPS-auto-triggered, not a chat Q&A). Deliberately different register from every other scenario: purely immersive, second-person, present-tense narration ("You're standing at X...") with **no practical facts** (price, hours, safety) - those belong to `single`/`safety`/`family_budget`. Meant to read like a museum audio guide, not a recommendation.

- **English**: built by reframing the real `description` field into second person - strips a leading repeat of the place's own name (handling both "X, a majestic cascade..." and "X stands as..." opening patterns) and prepends "It"/"It's" as needed so the result reads as a grammatically complete sentence, since the opener line already states "You're standing at X" and the description shouldn't repeat it.
- **Sinhala**: since there's no Sinhala description text to reframe, this is composed from structured facts only (category family, district, activities), grouped into category-specific templates (religious sites vs. waterfalls vs. beaches vs. tea estates vs. adventure parks) so the narration language actually fits what kind of place it is rather than one generic template repeated everywhere.

## Sinhala localization: place names and activities

Initial Sinhala output kept place names and activities in English regardless (e.g. "Dunhinda", "Swimming, Picnicking") since the dataset only has English text for these fields. Two modules now translate what can be translated correctly, without guessing at the rest:

- **`scripts/sinhala_activities.py`**: the `activities` field is free text (597 unique phrases across 1289 places, not a fixed vocabulary - ranges from "Swimming" to full sentences like "Explore the church's interior and learn about its history"). Two-tier lookup: ~50 hand-written common-phrase translations (covers the bulk of occurrences by frequency), then keyword-based matching for recurring concepts (prayer, photography, hiking, temple/church/kovil visits, tea, etc.) that catches most longer variants. ~96% of activity mentions get translated; the remaining ~4% (genuinely rare/long-tail phrases) fall back to the original English rather than a guessed translation.
- **`scripts/sinhala_names.py`**: place names are a real mix of English-origin ("St. Mary's Church", "Trinco Dive & Snorkel Centre"), Sinhala-origin ("Suriyawewa Rajamaha Viharaya", "Kirindiwela Falls"), and Tamil-origin (Hindu kovils, especially in Jaffna/Batticaloa - "Sri Pathirakali Amman Temple"). Decision: only translate the Sinhala-origin parts. This uses hand-written dictionaries (not algorithmic phonetic transliteration, which has a real error rate for a low-resource language) covering all 25 district names (100% accurate) plus ~25 common recurring Sinhala/Pali words (Viharaya, Devale, Ella, Wewa, etc.). English/Tamil words and any unmatched unique place-specific word are deliberately left untranslated. "Sri" is translated only when the name has no Tamil/Hindu marker word nearby (Kovil, Amman, Swami, Vinayagar, ...), since it's a shared Sanskrit-derived honorific in both traditions and translating it inside a Tamil name would be wrong. Output format is always `<partially-Sinhala name> (<original English name>)` so the original is never lost. ~36% of the 1289 names get some translation applied under this conservative scope.

## Growing the places dataset via OpenStreetMap (2278 -> ~5000)

`collect_osm_places.ipynb` pulls additional Sri Lankan points of interest from
**OpenStreetMap** (ODbL, attribution required: "© OpenStreetMap contributors")
via the free Overpass API, maps them onto the same schema as `places.json`,
and writes one `.jsonl` file per category (`osm_buddhist_temple.jsonl`,
`osm_waterfall.jsonl`, `osm_beach.jsonl`, etc. - matching the existing
one-file-per-category layout in `data/raw/`).

OSM gives real name/coordinates/category but no descriptive text, so each
place's `description` is generated by a small **local LLM**
(`Qwen2.5-3B-Instruct`, 4-bit quantized, free on a Kaggle T4 - no paid API
calls), prompted to use only the facts actually available (name, category,
district) and never invent history/prices/hours. If no GPU is available or
the model fails on a specific record, that record's description falls back
to a rule-based template instead - the pipeline still completes either way.

**Run it on Kaggle:**

1. **Upload the notebook** - kaggle.com -> Code -> New Notebook -> File ->
   Import Notebook -> select `collect_osm_places.ipynb`.
2. **Enable internet access** - right panel -> Settings -> **Internet: ON**
   (required for the Overpass API calls; off by default).
3. **Enable a GPU** - right panel -> Settings -> Accelerator -> **T4 x2** (or
   similar). Needed for the local LLM description step; without it the
   notebook still runs but every description falls back to the template.
4. **Upload `places.json` as a Kaggle Dataset** (so the notebook can dedupe
   against the 2278 places that already exist, instead of only deduping
   within its own run):
   - Kaggle -> **Datasets** -> **New Dataset**.
   - Drag in `data/processed/places.json`.
   - Title it something like `tripme-places`, set visibility to **Private**,
     click **Create**.
   - Back in the notebook, click **Add Input** (right panel) and attach the
     dataset you just created - it mounts at
     `/kaggle/input/tripme-places/places.json`.
   - In the notebook's setup cell, change:
     ```python
     EXISTING_PLACES_PATH = None
     ```
     to:
     ```python
     EXISTING_PLACES_PATH = Path("/kaggle/input/tripme-places/places.json")
     ```
     (match the path segment to whatever slug Kaggle generated for your
     dataset title). Re-run that cell and confirm it logs
     `Loaded 2278 existing places for dedup (active)`.
5. **Run All.** Fetches every (district x category) combination via Overpass
   (25 districts x 20 category filters, ~2s delay between calls - roughly
   15-20 minutes total) and is resumable if it disconnects partway through.
   The LLM loads once up front, then generates one description per place
   during the conversion step.
6. **Download the output files** - after the run, the right-side Output panel
   lists the `osm_*.jsonl` files. Download all of them into `data/raw/`.
7. **Re-merge locally:**
   ```bash
   python scripts/01_merge_places.py
   ```

**Caveats on the OSM-collected data** (all flagged via `id` prefix `pl_osm_`
for easy filtering later):
- `description` is LLM-generated from name/category/district only (or
  template-generated as a fallback) - reads naturally but won't have the
  specific historical/practical detail a hand-written description would.
- Visitor-logistics fields (`opening_hours`, `budget_category`,
  `safety_level`, etc.) are category-based defaults, not verified facts.
- OSM's actual Sri Lanka POI density means the final count landing near 5000
  isn't guaranteed - it depends on how much OSM coverage exists per category
  per district.

## Known open items

1. **Tamil**: not yet built. Same approach as Sinhala (hand-written templates grounded in place data, not machine translation) would apply, but needs a Tamil-capable base model equivalent to `ihalage/llama3-sinhala` - not yet researched.
2. **Sinhala/Tamil TTS**: not yet selected. Likely the riskiest unknown in the whole pipeline - evaluate providers (Google Cloud TTS, Azure, etc.) before building further on top of it.
3. **`lat`/`lng` in the dataset are unreliable** (only 295 unique pairs across 1289 places) - retrieval is district-based, not GPS-distance-based, on purpose.
4. **`family_friendly` is `"yes"` for all 1289 records** - not usable as a filter; excluded from retrieval filters and training templates.
5. Sinhala place-name/activity localization is intentionally conservative (see above) - genuinely untranslated English words mixed into Sinhala sentences are expected and normal (this also reflects how Sri Lankans actually speak - proper nouns and some terms commonly stay in English), not a bug, but the coverage gap is real and could be extended later with more dictionary entries if specific gaps turn out to matter in practice.

## Live Food Scanner - paused, not started

Explored fine-tuning an image-recognition model on Colab to identify Sri Lankan dishes from a photo (name + nutrition + cultural value, in the app's language). Researched available training data and found **no usable Sri Lankan food image dataset exists** - the only Sri-Lanka-labeled option found (a small Kaggle set) is unverified/likely too thin, and Sri-Lanka-unique dishes (kiribath, watalappan, lamprais, pol sambol) aren't covered by any adjacent South Asian dataset either. Training a classifier from scratch on real data isn't currently feasible without a substantial data collection effort first.

Decision: paused rather than forced with inadequate data. If revisited, the two realistic paths are (a) skip training entirely and call an existing multimodal vision API (e.g. Claude/GPT-4V) per-request to identify the dish and generate the explanation - no dataset needed, or (b) commit to a real data collection effort (self-photographing/crowdsourcing Sri Lankan dishes) before attempting to train a classifier.

## Running the pipeline

```bash
# 1. Download dataset (only needed once, or if the Drive folder changes)
python scripts/00_download_dataset.py

# 2. Merge + clean
python scripts/01_merge_places.py

# 3. Generate instruction datasets (English and Sinhala)
# (04_generate_instructions_si.py imports sinhala_activities.py and
# sinhala_names.py from the same scripts/ directory - no separate step needed)
python scripts/02_generate_instructions.py
python scripts/04_generate_instructions_si.py

# 4. Validate (checks all 4 files: train/val x en/si)
python scripts/03_validate_dataset.py
```

Then upload `data/training/{train,val,train_si,val_si}.jsonl` to Google Drive (e.g. `MyDrive/tripme/data/`) and run `notebooks/finetune_colab.ipynb` in Colab (free T4 GPU works, but expect a multi-hour run for the full 3-epoch pass over ~8.4k combined examples on an 8B model - likely spanning more than one Colab session).

After training, merge the LoRA adapter into the base model and convert to GGUF (see plan doc Step 7), place the result at `models/tripme-llama3-sinhala-q4_k_m.gguf`, then:

```bash
cd serve
pip install -r requirements.txt
uvicorn app:app --reload
```

Test without audio/STT/TTS via `POST /ask/text` with `{"question": "...", "district": "Kandy", "lang": "en"}` (or `"lang": "si"` with a Sinhala question).
