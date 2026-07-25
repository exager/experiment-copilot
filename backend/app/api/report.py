"""`POST /experiments/{id}/report` — persist the executive report.

Uses the latest statistics + recommendation to build a deterministic report.
When the LangGraph Report Agent is wired in, it can overwrite the summary /
next_steps via the same `report_service.persist(...)` call (the service
already overwrites existing rows).
"""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict, Field

from app.api.deps import ExperimentDep, SessionDep
from app.schemas.metrics import Recommendation
from app.schemas.report import ReportOut
from app.services import (
    metrics_service,
    recommendation_service,
    report_service,
    statistics_service,
)
from app.simulation.scheduler import _guardrail_regressed

router = APIRouter(prefix="/experiments", tags=["experiments"])


class GenerateReportRequest(BaseModel):
    """Optional overrides from an LLM Report Agent.

    If any field is omitted, the endpoint synthesizes a deterministic value
    from the current statistics + recommendation.
    """

    summary: str | None = Field(default=None, max_length=4000)
    business_impact: str | None = Field(default=None, max_length=1000)
    next_steps: list[str] | None = Field(default=None, max_length=10)
    recommendation: Recommendation | None = Field(default=None)

    model_config = ConfigDict(extra="forbid")


def _default_summary(experiment, stats, rec) -> str:
    hypothesis = (experiment.hypothesis or {}).get("hypothesis") or "the change"
    winner = stats.winner
    conf = (stats.confidence or 0.0) * 100
    lift = (stats.conversion_lift or 0.0) * 100
    if winner == "variant":
        return (
            f"Variant improved the primary metric by {lift:.1f}% at "
            f"{conf:.1f}% confidence, supporting the hypothesis: {hypothesis}."
        )
    if winner == "control":
        return (
            f"Control outperformed variant by {abs(lift):.1f}% at "
            f"{conf:.1f}% confidence; the hypothesis was not supported."
        )
    return (
        f"Results remain inconclusive (confidence {conf:.1f}%). "
        f"Consider extending the experiment or reviewing the design."
    )


def _default_next_steps(recommendation: Recommendation) -> list[str]:
    return {
        "scale": [
            "Roll out the variant to 100% of the targeted audience.",
            "Monitor guardrail metrics for two weeks post-launch.",
            "Document the win in the experiment log and share with stakeholders.",
        ],
        "continue": [
            "Continue collecting data until statistical significance is reached.",
            "Review guardrails weekly to ensure no regression is developing.",
        ],
        "stop": [
            "Stop the experiment; revert to the control experience.",
            "Investigate why variant underperformed before iterating.",
        ],
        "rollback": [
            "Immediately roll back the variant to protect user experience.",
            "Analyze the guardrail regression and design a corrective test.",
        ],
    }[recommendation]


@router.post(
    "/{experiment_id}/report",
    response_model=ReportOut,
    summary="Generate (and persist) the executive report",
)
def generate_report(
    experiment: ExperimentDep,
    session: SessionDep,
    overrides: GenerateReportRequest | None = None,
) -> ReportOut:
    stats = statistics_service.snapshot(session, experiment.id)
    latest = metrics_service.latest(session, experiment.id)
    sample_size = int((experiment.configuration or {}).get("sample_size") or 0)
    total_users = 0 if latest is None else latest.users_control + latest.users_variant
    sample_ratio = min(1.0, total_users / sample_size) if sample_size > 0 else 0.0
    guardrail_regressed = _guardrail_regressed(
        latest.guardrails if latest is not None else None
    )
    rec_out = recommendation_service.recommend(
        stats,
        guardrail_regressed=guardrail_regressed,
        sample_ratio=sample_ratio,
    )

    overrides = overrides or GenerateReportRequest()
    recommendation = overrides.recommendation or rec_out.recommendation
    summary = overrides.summary or _default_summary(experiment, stats, rec_out)
    next_steps = overrides.next_steps or _default_next_steps(recommendation)
    business_impact = overrides.business_impact

    report = report_service.persist(
        session,
        experiment_id=experiment.id,
        summary=summary,
        recommendation=recommendation,
        business_impact=business_impact,
        next_steps=next_steps,
        details={
            "statistics": stats.model_dump(),
            "sample_ratio": sample_ratio,
            "guardrail_regressed": guardrail_regressed,
        },
    )
    return ReportOut.model_validate(report)