"""Apply the Part 9 metric gate; human approval remains mandatory."""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
PART8 = ROOT / "reports" / "part08" / "corrective_eval" / "import_summary.json"
APPROVAL = ROOT / "reports" / "part09" / "human_approval.json"
OUTPUT = ROOT / "reports" / "part09" / "release_gate.json"
THRESHOLDS = {
    "complete_ending_rate_min": 0.98,
    "token_limit_hit_rate_max": 0.02,
    "place_name_coverage_min": 0.90,
    "scenario_relevance_rate_min": 0.95,
    "encoding_clean_rate_min": 1.0,
    "repetition_score_max": 0.05,
}


def main():
    if not PART8.is_file():
        raise FileNotFoundError("Part 8 must be imported before running Part 9")
    part8 = json.loads(PART8.read_text(encoding="utf-8"))
    metrics = part8["new_part08"]
    checks = {
        "complete_ending_rate": metrics["complete_ending_rate"] >= THRESHOLDS["complete_ending_rate_min"],
        "token_limit_hit_rate": metrics["token_limit_hit_rate"] <= THRESHOLDS["token_limit_hit_rate_max"],
        "place_name_coverage": metrics["mean_place_name_coverage"] >= THRESHOLDS["place_name_coverage_min"],
        "scenario_relevance_rate": metrics["scenario_relevance_rate"] >= THRESHOLDS["scenario_relevance_rate_min"],
        "encoding_clean_rate": metrics["encoding_clean_rate"] >= THRESHOLDS["encoding_clean_rate_min"],
        "repetition_score": metrics["mean_repetition_score"] <= THRESHOLDS["repetition_score_max"],
    }
    metric_gate = all(checks.values())
    human = json.loads(APPROVAL.read_text(encoding="utf-8")) if APPROVAL.is_file() else {}
    human_approved = human.get("status") == "approved" and bool(human.get("reviewer"))
    status = "release_candidate_approved" if metric_gate and human_approved else (
        "blocked_metric_gate_failed" if not metric_gate else "blocked_human_approval_pending"
    )
    report = {
        "status": status, "metric_gate_passed": metric_gate, "metric_checks": checks,
        "thresholds": THRESHOLDS, "human_approval_present": human_approved,
        "human_approval": human, "release_allowed": metric_gate and human_approved,
        "adapter": "artifacts/part07_corrective",
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
