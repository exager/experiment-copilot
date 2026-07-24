"""Schemas for the hypothesis-review interrupt step.

After the LangGraph pipeline runs `context_agent -> hypothesis_agent` and
pauses, the API returns a :class:`HypothesisReview`: the AI's problem
statement plus, for each metric role, the *full* catalog of eligible metrics
with a ``selected`` flag marking the AI's picks. This lets the UI render a
pre-checked checklist the user can adjust before launching.

Once the PM adjusts the checklist, :class:`HypothesisMetricUpdate` (mirroring
the same `{id, selected}` shape) carries the edited selection back to
`POST /experiments/{id}/validate`, which resumes the same graph thread.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from app.catalog import PRIMARY_METRICS, SECONDARY_METRICS
from app.schemas.experiment import Hypothesis


class MetricOption(BaseModel):
    """A single catalog metric, with whether the AI selected it for this role."""

    id: str
    label: str
    selected: bool


class HypothesisReview(BaseModel):
    """Response for `POST /context/{id}/hypothesis` (paused at the interrupt)."""

    thread_id: str
    experiment_id: int
    experiment_name: str
    hypothesis: str
    problem_statement: str
    context_understanding: dict
    primary_metric: list[MetricOption]
    secondary_metrics: list[MetricOption]
    guardrail_metrics: list[MetricOption]

    model_config = ConfigDict(extra="forbid")


class MetricToggle(BaseModel):
    """A single metric id + whether the PM wants it selected for that role."""

    id: str
    selected: bool


class HypothesisMetricUpdate(BaseModel):
    """Body for `POST /experiments/{id}/validate` when the PM edits metrics.

    Mirrors `HypothesisReview`'s `list[MetricOption]` shape (minus `label`,
    which the server doesn't need back). Both lists must cover exactly the
    catalog's eligible ids for that role; `primary_metric` must have exactly
    one `selected=True`, and that id must not also be selected in
    `secondary_metrics` (some ids are eligible for both roles — see
    `app/catalog/metrics.py`).
    """

    primary_metric: list[MetricToggle]
    secondary_metrics: list[MetricToggle]

    model_config = ConfigDict(extra="forbid")

    @field_validator("primary_metric")
    @classmethod
    def _check_primary(cls, v: list[MetricToggle]) -> list[MetricToggle]:
        if {m.id for m in v} != set(PRIMARY_METRICS):
            raise ValueError(f"primary_metric must cover exactly {sorted(PRIMARY_METRICS)}")
        if sum(m.selected for m in v) != 1:
            raise ValueError("primary_metric must have exactly one metric selected")
        return v

    @field_validator("secondary_metrics")
    @classmethod
    def _check_secondary(cls, v: list[MetricToggle]) -> list[MetricToggle]:
        if {m.id for m in v} != set(SECONDARY_METRICS):
            raise ValueError(f"secondary_metrics must cover exactly {sorted(SECONDARY_METRICS)}")
        return v

    @model_validator(mode="after")
    def _check_no_overlap(self) -> "HypothesisMetricUpdate":
        primary_id = next(m.id for m in self.primary_metric if m.selected)
        if any(m.id == primary_id and m.selected for m in self.secondary_metrics):
            raise ValueError(
                f"{primary_id!r} is selected as primary and cannot also be secondary"
            )
        return self

    def apply(self, hypothesis: dict) -> dict:
        """Return an updated hypothesis dict with the new metric selection.

        Re-validates through `Hypothesis` so the result is guaranteed to
        satisfy every existing invariant (catalog ids, no overlap, etc.).
        """
        primary_id = next(m.id for m in self.primary_metric if m.selected)
        secondary_ids = [m.id for m in self.secondary_metrics if m.selected]
        updated = {
            **hypothesis,
            "primary_metric": primary_id,
            "secondary_metrics": secondary_ids,
        }
        return Hypothesis(**updated).model_dump()
