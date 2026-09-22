"""Run the Part 12 metric gate. Human approval is always separate."""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "reports" / "part11" / "evaluation" / "comparison.json"
OUTPUT = ROOT / "reports" / "part12" / "release_gate.json"
THRESHOLDS = {
    "complete_ending_rate_min": 0.98,
    "token_limit_hit_rate_max": 0.02,
    "place_name_coverage_min": 0.90,
    "scenario_relevance_rate_min": 0.95,
    "encoding_clean_rate_min": 1.0,
    "repetition_score_max": 0.05,
}


def main():
    comparison = json.loads(SOURCE.read_text(encoding="utf-8"))
    metrics = comparison["part11"]
    checks = {
        "complete_ending_rate": metrics["complete_ending_rate"] >= THRESHOLDS["complete_ending_rate_min"],
        "token_limit_hit_rate": metrics["token_limit_hit_rate"] <= THRESHOLDS["token_limit_hit_rate_max"],
        "place_name_coverage": metrics["mean_place_name_coverage"] >= THRESHOLDS["place_name_coverage_min"],
        "scenario_relevance_rate": metrics["scenario_relevance_rate"] >= THRESHOLDS["scenario_relevance_rate_min"],
        "encoding_clean_rate": metrics["encoding_clean_rate"] >= THRESHOLDS["encoding_clean_rate_min"],
        "repetition_score": metrics["mean_repetition_score"] <= THRESHOLDS["repetition_score_max"],
    }
    report = {
        "status": "blocked_metric_gate_failed" if not all(checks.values()) else "blocked_human_approval_pending",
        "metric_gate_passed": all(checks.values()),
        "metric_checks": checks,
        "thresholds": THRESHOLDS,
        "human_approval_present": False,
        "release_allowed": False,
        "adapter": "artifacts/part10_corrective",
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
