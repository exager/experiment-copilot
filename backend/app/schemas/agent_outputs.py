"""Structured-output schemas for LangGraph agent nodes.

`HypothesisOutput`/`TrafficSplit`/`ExperimentConfigurationOutput` mirror
app.schemas.experiment.Hypothesis/TrafficSplit/ExperimentConfiguration
field-for-field. They're duplicated here (rather than imported) because
schemas/experiment.py imports `ExperimentStatus` from app.models.experiment,
which doesn't exist yet — importing anything from that module currently
raises ImportError. Once that model lands, switch agent code to import the
real classes from schemas/experiment.py and delete the mirrors below.
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


class HypothesisOutput(BaseModel):
    """Mirrors app.schemas.experiment.Hypothesis."""

    experiment_name: str
    hypothesis: str
    primary_metric: str
    secondary_metrics: list[str] = Field(default_factory=list)
    guardrail_metrics: list[str] = Field(default_factory=list)


class TrafficSplit(BaseModel):
    """Mirrors app.schemas.experiment.TrafficSplit."""

    control: float = Field(..., ge=0.0, le=1.0)
    variant: float = Field(..., ge=0.0, le=1.0)


class ExperimentConfigurationOutput(BaseModel):
    """Mirrors app.schemas.experiment.ExperimentConfiguration."""

    feature_flag: str
    audience: str
    traffic_split: TrafficSplit
    duration_days: int = Field(..., ge=1, le=365)
    sample_size: int = Field(..., ge=1)
    confidence_level: float = Field(default=0.95, ge=0.5, le=0.999)
    baseline_conversion_rate: float = Field(default=0.10, ge=0.0, le=1.0)
    expected_lift: float = Field(default=0.05, ge=-1.0, le=5.0)


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
