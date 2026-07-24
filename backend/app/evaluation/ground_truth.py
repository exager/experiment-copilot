"""
Deterministic ground-truth checks for agent outputs (Developer 4).

Fast, free, no LLM. Each check returns a dict with per-check booleans and an
overall 0.0-1.0 score. These assert the structural/quality guarantees the
enhanced prompts are supposed to produce.
"""

from __future__ import annotations

from typing import Any


def _score(checks: dict[str, bool]) -> dict[str, Any]:
    total = len(checks)
    passed = sum(1 for v in checks.values() if v)
    return {
        "checks": checks,
        "passed": passed,
        "total": total,
        "score": round(passed / total, 3) if total else 0.0,
    }


def _is_snake_case(value: str) -> bool:
    return bool(value) and value == value.lower() and " " not in value


def check_context_output(output: dict[str, Any], expected: dict[str, Any]) -> dict[str, Any]:
    checks: dict[str, bool] = {}
    for field in ("product_type", "business_goal_summary", "problem_identified",
                  "experiment_area", "target_users"):
        checks[f"field_{field}_present"] = bool(str(output.get(field, "")).strip())
    confidence = output.get("ai_confidence")
    checks["ai_confidence_in_range"] = isinstance(confidence, int) and 0 <= confidence <= 100
    return _score(checks)


def check_hypothesis_output(output: dict[str, Any], expected: dict[str, Any]) -> dict[str, Any]:
    checks: dict[str, bool] = {}

    if "name_contains" in expected:
        checks["name_relevant"] = expected["name_contains"].lower() in output.get(
            "experiment_name", ""
        ).lower()

    if "hypothesis_mentions" in expected:
        h = output.get("hypothesis", "").lower()
        for term in expected["hypothesis_mentions"]:
            checks[f"hypothesis_mentions_{term}"] = term.lower() in h

    if "min_guardrails" in expected:
        checks["enough_guardrails"] = len(output.get("guardrail_metrics", [])) >= expected["min_guardrails"]

    primary = output.get("primary_metric", "")
    checks["primary_metric_present"] = bool(primary)
    checks["primary_metric_snake_case"] = _is_snake_case(primary)
    checks["hypothesis_present"] = bool(output.get("hypothesis", "").strip())
    checks["secondary_metrics_non_empty"] = len(output.get("secondary_metrics", [])) > 0
    return _score(checks)


def check_configuration_output(output: dict[str, Any], expected: dict[str, Any]) -> dict[str, Any]:
    checks: dict[str, bool] = {}

    flag = output.get("feature_flag", "")
    checks["flag_snake_case"] = _is_snake_case(flag)
    checks["flag_exp_prefix"] = flag.startswith("exp_")

    split = output.get("traffic_split", {}) or {}
    control = split.get("control", 0.0)
    variant = split.get("variant", 0.0)
    checks["traffic_sums_to_one"] = abs((control + variant) - 1.0) < 0.01

    checks["duration_at_least_7"] = (output.get("duration_days") or 0) >= 7
    checks["sample_size_at_least_100"] = (output.get("sample_size") or 0) >= 100
    checks["confidence_level_valid"] = 0.8 <= (output.get("confidence_level") or 0) <= 0.999
    checks["audience_present"] = bool(str(output.get("audience", "")).strip())
    checks["baseline_rate_valid"] = 0.0 <= (output.get("baseline_conversion_rate") or -1) <= 1.0
    return _score(checks)


CHECKS = {
    "context": check_context_output,
    "hypothesis": check_hypothesis_output,
    "experiment_design": check_configuration_output,
}

# Which state key each agent writes its primary output under.
OUTPUT_KEY = {
    "context": "context_understanding",
    "hypothesis": "hypothesis",
    "experiment_design": "configuration",
}


def aggregate_scores(results: list[dict[str, Any]]) -> dict[str, Any]:
    if not results:
        return {"count": 0, "avg_score": 0.0, "min_score": 0.0, "max_score": 0.0}
    scores = [r["score"] for r in results]
    return {
        "count": len(scores),
        "avg_score": round(sum(scores) / len(scores), 3),
        "min_score": round(min(scores), 3),
        "max_score": round(max(scores), 3),
        "all_passed": all(s >= 0.7 for s in scores),
    }
