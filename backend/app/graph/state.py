"""Shared LangGraph state for the Experiment Copilot pipeline."""

from __future__ import annotations

from typing import TypedDict


class ExperimentState(TypedDict, total=False):
    # Input — mirrors app.schemas.context.ProductContextCreate field names.
    business_goal: str
    website: str | None
    current_flow: str | None
    feature: str | None
    pain_point: str | None

    # Populated by graph nodes, in pipeline order.
    context_understanding: dict | None
    hypothesis: dict | None
    configuration: dict | None
    validation: dict | None
    metrics: dict | None
    statistics: dict | None
    recommendation: dict | None
    report: dict | None

    errors: list[str]
