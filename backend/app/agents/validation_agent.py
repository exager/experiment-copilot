"""Validation Agent node.

Runs a deterministic rule engine over the experiment configuration, then
asks the LLM to explain the result in plain language. The LLM never
re-decides pass/fail — it only narrates the rule engine's decision.
"""

from __future__ import annotations

from pathlib import Path

from app.agents import llm
from app.agents.llm import with_retry
from app.schemas.agent_outputs import ValidationEnrichment
from app.schemas.validation import RuleResult, ValidationResult

_PROMPT = (Path(__file__).resolve().parent.parent / "prompts" / "validation.md").read_text()


def evaluate_rules(configuration: dict) -> ValidationResult:
    """Deterministic rule engine.

    TODO(Dev 2 / rules owner): move this into app/rules/ once the real
    rule engine exists there — this is a minimal stand-in so the graph has
    something runnable today.
    """
    traffic = configuration.get("traffic_split") or {}
    traffic_sum = (traffic.get("control") or 0) + (traffic.get("variant") or 0)

    results = [
        RuleResult(
            rule_id="traffic_split_sums_to_one",
            name="Traffic split sums to 1.0",
            matched=abs(traffic_sum - 1.0) < 1e-6,
            message=f"Traffic split sums to {traffic_sum:.2f}",
        ),
        RuleResult(
            rule_id="audience_defined",
            name="Audience is defined",
            matched=bool(configuration.get("audience")),
            message="Audience is set" if configuration.get("audience") else "Audience is missing",
        ),
        RuleResult(
            rule_id="duration_in_range",
            name="Duration is between 1 and 90 days",
            matched=1 <= (configuration.get("duration_days") or 0) <= 90,
            message=f"Duration is {configuration.get('duration_days')} days",
        ),
        RuleResult(
            rule_id="sample_size_positive",
            name="Sample size is positive",
            matched=(configuration.get("sample_size") or 0) > 0,
            message=f"Sample size is {configuration.get('sample_size')}",
        ),
        RuleResult(
            rule_id="feature_flag_defined",
            name="Feature flag is defined",
            matched=bool(configuration.get("feature_flag")),
            message="Feature flag is set" if configuration.get("feature_flag") else "Feature flag is missing",
        ),
    ]

    matched = [r for r in results if r.matched]
    rejected = [r for r in results if not r.matched]
    decision = "approve" if not rejected else "reject"

    return ValidationResult(
        rules_evaluated=results,
        rules_matched=matched,
        rules_rejected=rejected,
        decision=decision,
        explanation="",
    )


@with_retry
def node(state: dict) -> dict:
    configuration = state.get("configuration") or {}
    rule_result = evaluate_rules(configuration)

    prompt = _PROMPT.format(
        configuration=configuration,
        decision=rule_result.decision,
        rules_matched=[r.name for r in rule_result.rules_matched],
        rules_rejected=[r.name for r in rule_result.rules_rejected],
    )
    model = llm.get_llm().with_structured_output(ValidationEnrichment)
    enrichment: ValidationEnrichment = model.invoke(prompt)

    validation = rule_result.model_copy(
        update={
            "validation_score": enrichment.validation_score,
            "warnings": enrichment.warnings,
            "suggestions": enrichment.suggestions,
            "explanation": enrichment.explanation,
        }
    )
    return {"validation": validation.model_dump()}
