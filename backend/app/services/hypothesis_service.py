"""Service for the hypothesis-review interrupt step.

Runs the LangGraph pipeline for a given product context up to the
human-in-the-loop pause (right after `hypothesis_agent`) and shapes the paused
state into a :class:`HypothesisReview` the frontend can render.

A placeholder `Experiment` row is created up front (empty hypothesis/
configuration) so the graph thread is keyed by a real `experiment_id` from
the very first invoke — `POST /experiments/{id}/validate` resumes this same
thread once the PM confirms their metric selection.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.catalog.metrics import (
    GUARDRAIL_METRICS,
    METRICS,
    PRIMARY_METRICS,
    SECONDARY_METRICS,
)
from app.graph.builder import start_experiment
from app.schemas.hypothesis_review import HypothesisReview, MetricOption
from app.services import context_service, experiment_service


def _options(metric_ids: tuple[str, ...], selected: set[str]) -> list[MetricOption]:
    """Turn a role's catalog metric ids into `{id, label, selected}` options."""
    return [
        MetricOption(id=mid, label=METRICS[mid].label, selected=mid in selected)
        for mid in metric_ids
    ]


def build_review(state: dict, thread_id: str, experiment_id: int) -> HypothesisReview:
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
        experiment_id=experiment_id,
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

    # Placeholder row so the graph thread has a real experiment_id from the
    # start; hypothesis_agent.node fills in `hypothesis` as soon as it runs.
    experiment = experiment_service.create_draft(
        session, context_id=context_id, hypothesis={}, configuration={}
    )

    initial_state = {
        "business_goal": ctx.business_goal,
        "website": ctx.website,
        "current_flow": ctx.current_flow,
        "feature": ctx.feature,
        "pain_point": ctx.pain_point,
        "errors": [],
        "experiment_id": experiment.id,
        "context_id": context_id,
    }

    thread_id = str(experiment.id)
    state = start_experiment(thread_id, initial_state)
    return build_review(state, thread_id, experiment.id)
