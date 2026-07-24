"""Validation Agent node.

Runs the configurable rule engine (:mod:`app.rules`) over the experiment
configuration + hypothesis, then asks the LLM to explain the result in plain
language. The LLM never re-decides pass/fail — it only narrates the rule
engine's decision.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app.agents import llm
from app.agents.llm import with_retry
from app.rules import load_validation_engine
from app.schemas.agent_outputs import ValidationEnrichment
from app.schemas.validation import ValidationResult

_PROMPT = (Path(__file__).resolve().parent.parent / "prompts" / "validation.md").read_text()


def _rule_context(configuration: dict, hypothesis: dict | None) -> dict[str, Any]:
    """Shape state into the dot-path context the validation rules expect.

    The bundled rules reference a couple of *derived* fields
    (``configuration.traffic_split_sum`` and ``hypothesis.guardrail_count``),
    so we compute them here rather than pushing that into the JSON rules.
    """
    traffic = configuration.get("traffic_split") or {}
    traffic_sum = (traffic.get("control") or 0) + (traffic.get("variant") or 0)
    hyp = hypothesis or {}
    return {
        "configuration": {**configuration, "traffic_split_sum": traffic_sum},
        "hypothesis": {
            "primary_metric": hyp.get("primary_metric"),
            "guardrail_count": len(hyp.get("guardrail_metrics") or []),
        },
    }


def evaluate_rules(configuration: dict, hypothesis: dict | None = None) -> ValidationResult:
    """Evaluate the configuration/hypothesis against the shared rule engine."""
    return load_validation_engine().evaluate(_rule_context(configuration, hypothesis))


@with_retry
def node(state: dict) -> dict:
    configuration = state.get("configuration") or {}
    hypothesis = state.get("hypothesis") or {}
    rule_result = evaluate_rules(configuration, hypothesis)

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
