"""Pydantic schemas for rule-engine validation results.

Every validation response includes:
  - rules_evaluated: every rule the engine considered
  - rules_matched:   rules whose conditions were satisfied
  - rules_rejected:  rules whose conditions were NOT satisfied
  - decision:        final decision label (e.g. "approve", "reject", "warn")
  - explanation:     human-readable summary
  - warnings/suggestions/score: enriched by the Validation Agent
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class RuleResult(BaseModel):
    """Outcome of evaluating a single rule."""

    rule_id: str
    name: str
    priority: int = 0
    matched: bool
    decision: str | None = None
    message: str | None = None
    details: dict[str, Any] = Field(default_factory=dict)


class ValidationResult(BaseModel):
    """Full validation response — engine output + AI enrichment."""

    rules_evaluated: list[RuleResult] = Field(default_factory=list)
    rules_matched: list[RuleResult] = Field(default_factory=list)
    rules_rejected: list[RuleResult] = Field(default_factory=list)
    decision: str
    explanation: str

    # Optional AI-enriched fields (populated by the Validation Agent).
    validation_score: float | None = Field(default=None, ge=0.0, le=1.0)
    warnings: list[str] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class ValidationRequest(BaseModel):
    """Body for `POST /validate`."""

    experiment_id: int