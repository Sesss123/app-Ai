"""Create a leakage-free, conservative Sinhala pilot-training candidate set.

This output is a review candidate, not automatically approved training data.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
EVAL_DIR = ROOT / "data" / "evaluation" / "gold_v0.1.0"
OUTPUT = ROOT / "data" / "training" / "pilot_v0.1.0"
SOURCE_FILES = (ROOT / "data" / "training" / "train_si.jsonl", ROOT / "data" / "training" / "val_si.jsonl")
ALLOWED_SCENARIOS = {"single", "compare", "itinerary", "daytrip", "itinerary_multi", "trip_plan_structured"}
SCENARIO_CAPS = {"single": 500, "compare": 140, "itinerary": 140, "daytrip": 140, "itinerary_multi": 90, "trip_plan_structured": 90}
RISK_RE = re.compile(r"\b(safe|safety|ticket|price|open|opening|weather|road condition)\b", re.I)


def stable_key(row: dict) -> str:
    return hashlib.sha256(("42|" + json.dumps(row, ensure_ascii=False, sort_keys=True)).encode("utf-8")).hexdigest()


class UnionFind:
    def __init__(self) -> None:
        self.parent = {}
    def find(self, value):
        self.parent.setdefault(value, value)
        if self.parent[value] != value:
            self.parent[value] = self.find(self.parent[value])
        return self.parent[value]
    def union(self, first, second):
        a, b = self.find(first), self.find(second)
        if a != b:
            self.parent[b] = a


def write_jsonl(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def main() -> None:
    holdout = set((EVAL_DIR / "holdout_place_ids.txt").read_text(encoding="utf-8").split())
    registry = ROOT / "data" / "registry" / "place_registry_v0.1.0.jsonl"
    eligible = {json.loads(line)["canonical_place_id"] for line in registry.read_text(encoding="utf-8").splitlines() if line.strip()} - holdout
    rows = []
    for path in SOURCE_FILES:
        rows.extend(json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip())

    rejected, candidates = [], []
    for row in rows:
        reasons = []
        ids = set(row.get("place_ids") or [])
        if row.get("scenario") not in ALLOWED_SCENARIOS:
            reasons.append("scenario_not_approved")
        if not ids:
            reasons.append("no_place_grounding")
        if ids & holdout:
            reasons.append("gold_holdout_leakage")
        if ids and not ids <= eligible:
            reasons.append("place_not_osm_attributed")
        assistant_text = " ".join(message.get("content", "") for message in row.get("messages", []) if message.get("role") == "assistant")
        if RISK_RE.search(assistant_text):
            reasons.append("mutable_fact_keyword_review")
        if reasons:
            rejected.append({"reasons": sorted(set(reasons)), "row": row})
        else:
            candidates.append(row)

    candidates.sort(key=stable_key)
    selected, counts = [], Counter()
    for row in candidates:
        scenario = row["scenario"]
        if counts[scenario] < SCENARIO_CAPS[scenario]:
            selected.append(row); counts[scenario] += 1

    uf = UnionFind()
    for row in selected:
        ids = row["place_ids"]
        for value in ids[1:]:
            uf.union(ids[0], value)
    components = defaultdict(list)
    for row in selected:
        components[uf.find(row["place_ids"][0])].append(row)
    ordered = sorted(components.items(), key=lambda item: hashlib.sha256(f"42|{item[0]}".encode()).hexdigest())
    train, validation = [], []
    target_train = int(len(selected) * 0.9)
    for _, component_rows in ordered:
        (train if len(train) < target_train else validation).extend(component_rows)

    OUTPUT.mkdir(parents=True, exist_ok=True)
    write_jsonl(OUTPUT / "pilot_train_candidate.jsonl", train)
    write_jsonl(OUTPUT / "pilot_validation_candidate.jsonl", validation)
    write_jsonl(OUTPUT / "rejected_examples.jsonl", rejected)
    train_ids = {value for row in train for value in row["place_ids"]}
    val_ids = {value for row in validation for value in row["place_ids"]}
    summary = {
        "status": "candidate_requires_human_review",
        "source_rows": len(rows), "eligible_before_caps": len(candidates),
        "pilot_train_rows": len(train), "pilot_validation_rows": len(validation),
        "scenario_counts": dict(Counter(row["scenario"] for row in selected)),
        "holdout_overlap": len((train_ids | val_ids) & holdout),
        "train_validation_place_overlap": len(train_ids & val_ids),
        "rejected_rows": len(rejected),
        "rejection_reason_counts": dict(Counter(reason for item in rejected for reason in item["reasons"]))
    }
    (OUTPUT / "pilot_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    if summary["holdout_overlap"] or summary["train_validation_place_overlap"]:
        raise SystemExit("Leakage validation failed")


if __name__ == "__main__":
    main()

