"""Service for the hypothesis-review interrupt step.

Runs the LangGraph pipeline for a given product context up to the
human-in-the-loop pause (right after `hypothesis_agent`) and shapes the paused
state into a :class:`HypothesisReview` the frontend can render.
"""

from __future__ import annotations

from uuid import uuid4

from sqlalchemy.orm import Session

from app.catalog.metrics import (
    GUARDRAIL_METRICS,
    METRICS,
    PRIMARY_METRICS,
    SECONDARY_METRICS,
)
from app.graph.builder import start_experiment
from app.schemas.hypothesis_review import HypothesisReview, MetricOption
from app.services import context_service


def _options(metric_ids: tuple[str, ...], selected: set[str]) -> list[MetricOption]:
    """Turn a role's catalog metric ids into `{id, label, selected}` options."""
    return [
        MetricOption(id=mid, label=METRICS[mid].label, selected=mid in selected)
        for mid in metric_ids
    ]


def build_review(state: dict, thread_id: str) -> HypothesisReview:
    """Shape a paused graph state into a `HypothesisReview`."""
    hypothesis = state.get("hypothesis") or {}
    context_understanding = state.get("context_understanding") or {}

    primary_selected = (
        {hypothesis["primary_metric"]} if hypothesis.get("primary_metric") else set()
    )
    secondary_selected = set(hypothesis.get("secondary_metrics") or [])
    guardrail_selected = set(hypothesis.get("guardrail_metrics") or [])

    return HypothesisReview(
        thread_id=thread_id,
        experiment_name=hypothesis.get("experiment_name", ""),
        hypothesis=hypothesis.get("hypothesis", ""),
        problem_statement=context_understanding.get("problem_identified", ""),
        context_understanding=context_understanding,
        primary_metric=_options(PRIMARY_METRICS, primary_selected),
        secondary_metrics=_options(SECONDARY_METRICS, secondary_selected),
        guardrail_metrics=_options(GUARDRAIL_METRICS, guardrail_selected),
    )


def generate_review(session: Session, context_id: int) -> HypothesisReview:
    """Run context -> hypothesis for `context_id` and return the paused review."""
    ctx = context_service.get(session, context_id)

    initial_state = {
        "business_goal": ctx.business_goal,
        "website": ctx.website,
        "current_flow": ctx.current_flow,
        "feature": ctx.feature,
        "pain_point": ctx.pain_point,
        "errors": [],
    }

    thread_id = f"ctx-{context_id}-{uuid4().hex[:8]}"
    state = start_experiment(thread_id, initial_state)
    return build_review(state, thread_id)
