"""Schemas for the hypothesis-review interrupt step.

After the LangGraph pipeline runs `context_agent -> hypothesis_agent` and
pauses, the API returns a :class:`HypothesisReview`: the AI's problem
statement plus, for each metric role, the *full* catalog of eligible metrics
with a ``selected`` flag marking the AI's picks. This lets the UI render a
pre-checked checklist the user can adjust before launching.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class MetricOption(BaseModel):
    """A single catalog metric, with whether the AI selected it for this role."""

    id: str
    label: str
    selected: bool


class HypothesisReview(BaseModel):
    """Response for `POST /context/{id}/hypothesis` (paused at the interrupt)."""

    thread_id: str
    experiment_name: str
    hypothesis: str
    problem_statement: str
    context_understanding: dict
    primary_metric: list[MetricOption]
    secondary_metrics: list[MetricOption]
    guardrail_metrics: list[MetricOption]

    model_config = ConfigDict(extra="forbid")
