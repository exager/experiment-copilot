"""Pydantic schemas for metrics, statistics, and recommendations."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class MetricPoint(BaseModel):
    """A single metrics snapshot as returned by the API."""

    id: int
    experiment_id: int
    users_control: int
    users_variant: int
    conversion_control: int
    conversion_variant: int
    revenue_control: float
    revenue_variant: float
    confidence: float | None = None
    p_value: float | None = None
    conversion_lift: float | None = None
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)


class StatisticsOut(BaseModel):
    """Derived statistics for the current experiment state."""

    p_value: float | None = None
    confidence: float | None = None
    conversion_lift: float | None = None
    z_score: float | None = None
    control_conversion_rate: float | None = None
    variant_conversion_rate: float | None = None
    winner: Literal["control", "variant", "inconclusive"] = "inconclusive"
    is_significant: bool = False


Recommendation = Literal["scale", "continue", "stop", "rollback"]


class RecommendationOut(BaseModel):
    """Decision recommendation for the current experiment state."""

    recommendation: Recommendation
    rationale: str
    confidence: float = Field(..., ge=0.0, le=1.0)


class MetricsSnapshot(BaseModel):
    """Combined payload returned by `GET /experiment/{id}/metrics`."""

    experiment_id: int
    latest: MetricPoint | None
    series: list[MetricPoint] = Field(default_factory=list)
    statistics: StatisticsOut
    recommendation: RecommendationOut | None = None