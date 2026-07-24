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
    # Persist rule-engine portion; AI narration merges in later.
    experiment_service.mark_validated(session, experiment_id, result.model_dump())
    return result