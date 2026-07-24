"""Pydantic schemas for experiments, hypotheses, and configurations.

These mirror the JSON blobs that the AI agents produce and that the
Experiment model persists.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.experiment import ExperimentStatus


# ---------- Hypothesis ----------


class Hypothesis(BaseModel):
    """Output of the Hypothesis Agent."""

    experiment_name: str
    hypothesis: str
    primary_metric: str
    secondary_metrics: list[str] = Field(default_factory=list)
    guardrail_metrics: list[str] = Field(default_factory=list)


# ---------- Configuration ----------


class TrafficSplit(BaseModel):
    control: float = Field(..., ge=0.0, le=1.0)
    variant: float = Field(..., ge=0.0, le=1.0)


class ExperimentConfiguration(BaseModel):
    """Output of the Experiment Design Agent."""

    feature_flag: str
    audience: str
    traffic_split: TrafficSplit
    duration_days: int = Field(..., ge=1, le=365)
    sample_size: int = Field(..., ge=1)
    confidence_level: float = Field(default=0.95, ge=0.5, le=0.999)

    # Baseline assumptions used by the simulator.
    baseline_conversion_rate: float = Field(default=0.10, ge=0.0, le=1.0)
    expected_lift: float = Field(default=0.05, ge=-1.0, le=5.0)


# ---------- Draft / persisted experiment ----------


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