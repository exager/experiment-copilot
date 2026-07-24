"""Pydantic schemas for the Product Context resource."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ProductContextCreate(BaseModel):
    """Request body for `POST /context`."""

    business_goal: str = Field(..., min_length=1, max_length=2000)
    website: str | None = Field(default=None, max_length=512)
    current_flow: str | None = Field(default=None, max_length=4000)
    feature: str | None = Field(default=None, max_length=256)
    pain_point: str | None = Field(default=None, max_length=4000)


class ProductContextOut(BaseModel):
    """Response representation of a persisted ProductContext."""

    id: int
    business_goal: str
    website: str | None
    current_flow: str | None
    feature: str | None
    pain_point: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)