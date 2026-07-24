"""Pydantic schemas for the executive report."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.metrics import Recommendation


class ReportOut(BaseModel):
    """Executive report returned by `POST /report/{id}`."""

    id: int
    experiment_id: int
    summary: str
    recommendation: Recommendation
    business_impact: str | None = None
    next_steps: list[str] = Field(default_factory=list)
    details: dict | None = None
    generated_at: datetime

    model_config = ConfigDict(from_attributes=True)