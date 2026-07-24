"""Validation service — runs the rule engine against an experiment draft.

Flattens the experiment's `hypothesis` + `configuration` JSON blobs into a
context the rule engine understands, runs `load_validation_engine`, and
persists the result onto `Experiment.validation`.

AI enrichment (validation_score, warnings, suggestions, LLM explanation)
is Developer 4's Validation Agent's job. This service produces only the
deterministic rule-engine portion.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.rules import load_validation_engine
from app.schemas.validation import ValidationResult
from app.services import experiment_service


def deterministic_score(result: ValidationResult) -> float:
    """Compute a launch-readiness score from the rule result alone.

    Used as a fallback when the LLM enrichment (which normally sets
    `validation_score`) is unavailable — e.g. the Gemini quota is exhausted.
    Bands mirror `app/prompts/validation.md`: reject < 0.4, approve >= 0.85.
    """
    total = len(result.rules_evaluated) or 1
    ratio = len(result.rules_matched) / total
    if result.decision == "reject":
        return round(min(0.39, 0.4 * ratio), 2)
    if result.decision == "warn":
        return round(0.5 + 0.2 * ratio, 2)  # ~0.5-0.7
    return round(0.85 + 0.15 * ratio, 2)  # approve ~0.85-1.0


def _build_context(hypothesis: dict, configuration: dict) -> dict:
    """Flatten the JSON blobs into the shape the validation rules expect."""
    traffic = configuration.get("traffic_split") or {}
    traffic_sum = float(traffic.get("control", 0) or 0) + float(
        traffic.get("variant", 0) or 0
    )
    guardrails = hypothesis.get("guardrail_metrics") or []
    return {
        "hypothesis": {
            "primary_metric": hypothesis.get("primary_metric"),
            "guardrail_count": len(guardrails),
        },
        "configuration": {
            "feature_flag": configuration.get("feature_flag"),
            "audience": configuration.get("audience"),
            "traffic_split": {
                "control": float(traffic.get("control", 0) or 0),
                "variant": float(traffic.get("variant", 0) or 0),
            },
            "traffic_split_sum": traffic_sum,
            "duration_days": int(configuration.get("duration_days") or 0),
            "sample_size": int(configuration.get("sample_size") or 0),
            "confidence_level": float(configuration.get("confidence_level") or 0.0),
        },
    }


def validate(session: Session, experiment_id: int) -> ValidationResult:
    """Run the rule engine on an experiment and persist the result.

    Returns the ValidationResult so the caller (route or agent) can enrich
    it with LLM-generated narration before returning to the client.
    """
    exp = experiment_service.get(session, experiment_id)
    ctx = _build_context(exp.hypothesis or {}, exp.configuration or {})
    result = load_validation_engine().evaluate(ctx)
    # Fill a deterministic score + warnings so the result is never returned with
    # a null score / empty guidance; the AI narration overrides these later when
    # the Validation Agent's LLM enrichment succeeds.
    result.validation_score = deterministic_score(result)
    result.warnings = [r.message for r in result.rules_rejected if r.message]
    experiment_service.mark_validated(session, experiment_id, result.model_dump())
    return result