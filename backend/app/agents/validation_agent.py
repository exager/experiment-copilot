"""Validation Agent node.

Runs the configurable, JSON-driven rule engine (`app.rules`, loaded from
`validation_rules.json`) over the experiment configuration and hypothesis,
then asks the LLM to explain the result in plain language. The LLM never
re-decides pass/fail — it only narrates the rule engine's decision.

When this node is part of a persisted graph run (`experiment_id` in state),
the deterministic pass is delegated to `validation_service.validate` (which
reads the already-persisted configuration/hypothesis and persists its
result) instead of `evaluate_rules` below, so there's a single source of
truth for the rule evaluation + `Experiment.validation` write.
"""

from __future__ import annotations

from pathlib import Path

from app.agents import llm
from app.agents.db import maybe_session
from app.agents.llm import with_retry
from app.rules import load_validation_engine
from app.schemas.agent_outputs import ValidationEnrichment
from app.schemas.validation import ValidationResult
from app.services import experiment_service, validation_service

_PROMPT = (Path(__file__).resolve().parent.parent / "prompts" / "validation.md").read_text()


def evaluate_rules(configuration: dict, hypothesis: dict | None = None) -> ValidationResult:
    """Evaluate a configuration + hypothesis against `validation_rules.json`.

    Derives the two computed fields the rule set needs beyond the raw
    blobs: `configuration.traffic_split_sum` and `hypothesis.guardrail_count`.
    """
    hypothesis = hypothesis or {}
    traffic = configuration.get("traffic_split") or {}

    context = {
        "configuration": {
            **configuration,
            "traffic_split_sum": (traffic.get("control") or 0) + (traffic.get("variant") or 0),
        },
        "hypothesis": {
            **hypothesis,
            "guardrail_count": len(hypothesis.get("guardrail_metrics") or []),
        },
    }
    return load_validation_engine().evaluate(context)


@with_retry
def node(state: dict) -> dict:
    configuration = state.get("configuration") or {}
    hypothesis = state.get("hypothesis") or {}

    with maybe_session(state) as session:
        if session is not None:
            rule_result = validation_service.validate(session, state["experiment_id"])
        else:
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

        if session is not None:
            experiment_service.mark_validated(
                session, state["experiment_id"], validation.model_dump()
            )

    return {"validation": validation.model_dump()}
