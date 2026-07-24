"""Structured-output schemas for LangGraph agent nodes.

These are the *narration* schemas the LLM fills in — the parts of an agent's
output that don't map onto a catalog-validated, persisted field. The
structured hypothesis and experiment-configuration outputs use the real,
catalog-validated schemas in :mod:`app.schemas.experiment`
(``Hypothesis`` / ``ExperimentConfiguration``) directly, so there is a single
source of truth for those and the LLM can only emit catalog-valid values.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class ContextUnderstanding(BaseModel):
    """Output of the Product Context node — powers the "AI Understanding" card."""

    product_type: str
    business_goal_summary: str
    problem_identified: str
    experiment_area: str
    target_users: str
    ai_confidence: int = Field(..., ge=0, le=100)


class ValidationEnrichment(BaseModel):
    """LLM-filled portion of app.schemas.validation.ValidationResult.

    The rule-engine fields (rules_evaluated/rules_matched/rules_rejected/
    decision) are computed deterministically by evaluate_rules() in
    validation_agent.py and are not part of this schema.
    """

    validation_score: float = Field(..., ge=0.0, le=1.0)
    warnings: list[str] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)
    explanation: str


class RationaleOutput(BaseModel):
    """LLM-filled `rationale` field of app.schemas.metrics.RecommendationOut.

    The recommendation category and confidence are computed deterministically
    by decide_recommendation() in explanation_agent.py and are not part of
    this schema.
    """

    rationale: str


class ReportNarrative(BaseModel):
    """LLM-filled portion of app.schemas.report.ReportOut.

    recommendation/business_impact are computed deterministically and
    merged in by report_agent.node, not part of this schema.
    """

    summary: str
    next_steps: list[str] = Field(default_factory=list)
