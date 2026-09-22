"""Build the provisional Part 6 Kaggle evaluation package."""

import hashlib
import json
import random
import shutil
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
GOLD = ROOT / "data" / "evaluation" / "gold_v0.1.0" / "gold_500_ai_draft.jsonl"
HOLDOUT_IDS = ROOT / "data" / "evaluation" / "gold_v0.1.0" / "holdout_place_ids.txt"
TRAIN = ROOT / "data" / "training" / "pilot_v0.2.0" / "review" / "second_checked_train_candidate.jsonl"
VALIDATION = ROOT / "data" / "training" / "pilot_v0.2.0" / "review" / "second_checked_validation_candidate.jsonl"
ADAPTER = ROOT / "artifacts" / "part05_pilot"
OUTPUT = ROOT / "kaggle_upload" / "tripme-part06-provisional-eval"
SAMPLE_OUTPUT = OUTPUT / "provisional_gold_eval_120.jsonl"
SEED = 42
LANG_TARGETS = {"si": 60, "singlish": 30, "en": 30}


def load_jsonl(path: Path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def allocate(total: int, counts: dict[str, int]) -> dict[str, int]:
    available = sum(counts.values())
    raw = {key: total * value / available for key, value in counts.items()}
    result = {key: min(counts[key], int(value)) for key, value in raw.items()}
    remaining = total - sum(result.values())
    order = sorted(counts, key=lambda key: (raw[key] - int(raw[key]), counts[key]), reverse=True)
    while remaining:
        for key in order:
            if result[key] < counts[key]:
                result[key] += 1
                remaining -= 1
                if not remaining:
                    break
    return result


def system_prompt(language: str, required_facts: list[str]) -> str:
    facts = "\n".join(f"- {fact}" for fact in required_facts)
    if language == "si":
        intro = "ඔබ TripMe ශ්‍රී ලංකා සංචාරක සහායකයාය. පහත ලබාදී ඇති කරුණු පමණක් භාවිතා කරන්න. නොදන්නා වත්මන් තොරතුරු අනුමාන නොකරන්න."
    elif language == "singlish":
        intro = "Oba TripMe Sri Lanka travel assistant. Pahatha dila thiyena facts witharak use karanna. Nodanna current facts guess karanna epa."
    else:
        intro = "You are the TripMe Sri Lanka travel assistant. Use only the facts below and do not guess current information."
    return f"{intro}\nKnown facts:\n{facts}"


def main() -> None:
    rows = load_jsonl(GOLD)
    train_rows = load_jsonl(TRAIN) + load_jsonl(VALIDATION)
    holdout = {line.strip() for line in HOLDOUT_IDS.read_text(encoding="utf-8").splitlines() if line.strip()}
    training_ids = {place_id for row in train_rows for place_id in row["place_ids"]}
    overlap = holdout & training_ids
    if overlap:
        raise ValueError(f"Gold holdout leakage detected: {len(overlap)} IDs")

    grouped = defaultdict(list)
    for row in rows:
        grouped[(row["language"], row["scenario"])].append(row)
    rng = random.Random(SEED)
    selected = []
    for language, target in LANG_TARGETS.items():
        scenario_counts = {
            scenario: len(values)
            for (lang, scenario), values in grouped.items()
            if lang == language
        }
        quotas = allocate(target, scenario_counts)
        for scenario, quota in quotas.items():
            candidates = list(grouped[(language, scenario)])
            rng.shuffle(candidates)
            selected.extend(candidates[:quota])
    rng.shuffle(selected)
    assert len(selected) == 120

    prepared = []
    for row in selected:
        item = dict(row)
        item["system_prompt"] = system_prompt(row["language"], row["required_facts"])
        item["evaluation_status"] = "provisional_ai_draft_not_human_gold"
        prepared.append(item)

    if OUTPUT.exists():
        shutil.rmtree(OUTPUT)
    (OUTPUT / "adapter").mkdir(parents=True)
    SAMPLE_OUTPUT.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in prepared) + "\n", encoding="utf-8"
    )
    for path in ADAPTER.iterdir():
        if path.is_file():
            shutil.copy2(path, OUTPUT / "adapter" / path.name)

    summary = {
        "status": "provisional_eval_ready_not_human_gold",
        "rows": len(prepared),
        "seed": SEED,
        "language_counts": dict(Counter(row["language"] for row in prepared)),
        "scenario_counts": dict(Counter(row["scenario"] for row in prepared)),
        "gold_holdout_training_overlap": len(overlap),
        "warning": "References are AI drafts and must not be reported as human-approved gold labels.",
    }
    (OUTPUT / "evaluation_sample_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    metadata = {
        "title": "TripMe Part 06 Provisional Gold Evaluation",
        "id": "YOUR_KAGGLE_USERNAME/tripme-part06-provisional-eval",
        "licenses": [{"name": "other"}],
    }
    (OUTPUT / "dataset-metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    package = {
        **summary,
        "sample_sha256": sha256(SAMPLE_OUTPUT),
        "adapter_config_present": (OUTPUT / "adapter" / "adapter_config.json").is_file(),
        "adapter_weights_present": (OUTPUT / "adapter" / "adapter_model.safetensors").is_file(),
    }
    (OUTPUT / "package_manifest.json").write_text(json.dumps(package, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(package, ensure_ascii=False, indent=2))
    print(f"Prepared: {OUTPUT}")


if __name__ == "__main__":
    main()
