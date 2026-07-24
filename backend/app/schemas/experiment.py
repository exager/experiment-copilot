"""Pydantic schemas for experiments, hypotheses, and configurations.

These mirror the JSON blobs the AI agents produce and that the Experiment
model persists. All catalog-backed fields (audience / metrics / traffic
split) are validated so the LLM cannot invent unknown values.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.catalog import (
    Audience,
    ExperimentStatus,
    TrafficSplitOption,
    get_split,
    is_valid_guardrail,
    is_valid_primary,
    is_valid_secondary,
)


# ---------- Hypothesis ------------------------------------------------------


class Hypothesis(BaseModel):
    """Output of the Hypothesis Agent."""

    experiment_name: str = Field(..., min_length=3, max_length=120)
    hypothesis: str = Field(..., min_length=10, max_length=2000)
    primary_metric: str
    secondary_metrics: list[str] = Field(default_factory=list, max_length=5)
    guardrail_metrics: list[str] = Field(default_factory=list, max_length=5)

    @field_validator("primary_metric")
    @classmethod
    def _check_primary(cls, v: str) -> str:
        if not is_valid_primary(v):
            raise ValueError(
                f"primary_metric {v!r} is not a valid primary-eligible metric"
            )
        return v

    @field_validator("secondary_metrics")
    @classmethod
    def _check_secondaries(cls, v: list[str]) -> list[str]:
        bad = [m for m in v if not is_valid_secondary(m)]
        if bad:
            raise ValueError(
                f"secondary_metrics contain unsupported ids: {bad}"
            )
        return v

    @field_validator("guardrail_metrics")
    @classmethod
    def _check_guardrails(cls, v: list[str]) -> list[str]:
        bad = [m for m in v if not is_valid_guardrail(m)]
        if bad:
            raise ValueError(
                f"guardrail_metrics contain unsupported ids: {bad}"
            )
        return v

    @model_validator(mode="after")
    def _check_no_overlap(self) -> "Hypothesis":
        if self.primary_metric in self.secondary_metrics:
            raise ValueError(
                "primary_metric must not also appear in secondary_metrics"
            )
        return self


# ---------- Configuration ---------------------------------------------------


class TrafficSplit(BaseModel):
    """Concrete control/variant fractions."""

    control: float = Field(..., ge=0.0, le=1.0)
    variant: float = Field(..., ge=0.0, le=1.0)


class ExperimentConfiguration(BaseModel):
    """Output of the Experiment Design Agent.

    Catalog-constrained fields:
      - `audience` picks from `Audience`.
      - `traffic_split_option` picks from `TrafficSplitOption`; the concrete
        `traffic_split` (fractions) is derived automatically.
      - `duration_days` and `confidence_level` are unconstrained here (the
        rule engine validates them), so PMs can enter custom values.
    """

    feature_flag: str = Field(..., min_length=3, max_length=64)
    audience: Audience
    traffic_split_option: TrafficSplitOption = Field(
        default=TrafficSplitOption.SPLIT_50_50
    )
    traffic_split: TrafficSplit | None = Field(default=None)
    duration_days: int = Field(..., ge=1, le=365)
    sample_size: int = Field(..., ge=1)
    confidence_level: float = Field(default=0.95, ge=0.5, le=0.999)

    # Baseline assumptions used by the simulator.
    baseline_conversion_rate: float = Field(default=0.10, ge=0.0, le=1.0)
    expected_lift: float = Field(default=0.05, ge=-1.0, le=5.0)

    @model_validator(mode="after")
    def _derive_traffic_split(self) -> "ExperimentConfiguration":
        """Always keep `traffic_split` in sync with `traffic_split_option`."""
        control, variant = get_split(self.traffic_split_option)
        self.traffic_split = TrafficSplit(control=control, variant=variant)
        return self


# ---------- Draft / persisted experiment ------------------------------------


class ExperimentDraft(BaseModel):
    """Payload returned by `POST /context` — a full draft ready for review."""

    experiment_id: int
    context_id: int
    hypothesis: Hypothesis
    configuration: ExperimentConfiguration
    status: ExperimentStatus


class ExperimentOut(BaseModel):
    """Full persisted experiment representation."""

    id: int
    context_id: int
    hypothesis: dict
    configuration: dict
    validation: dict | None
    status: ExperimentStatus
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class LaunchRequest(BaseModel):
    """Body for `POST /experiment/start`."""

    experiment_id: int