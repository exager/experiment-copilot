"""Report service — persists the final executive report.

The prose (summary, next_steps) comes from Developer 4's Report Agent.
This service just wraps the DB insert + the deterministic fields (the
recommendation string comes from the recommendation service, business
impact is either handed in by the agent or synthesized from statistics).
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.catalog.status import ExperimentStatus
from app.models.report import Report
from app.schemas.metrics import Recommendation
from app.services import experiment_service
from app.utils.errors import ConflictError, NotFoundError


def get(session: Session, experiment_id: int) -> Report:
    row = (
        session.query(Report)
        .filter(Report.experiment_id == experiment_id)
        .one_or_none()
    )
    if row is None:
        raise NotFoundError(
            f"Report for experiment {experiment_id} not found",
            details={"experiment_id": experiment_id},
        )
    return row


def persist(
    session: Session,
    *,
    experiment_id: int,
    summary: str,
    recommendation: Recommendation,
    business_impact: str | None = None,
    next_steps: list[str] | None = None,
    details: dict | None = None,
) -> Report:
    """Create or replace the report row for an experiment.

    The parent experiment is transitioned to COMPLETED (idempotent) so the
    dashboard reflects the finished state. If a report already exists, it's
    overwritten — reports are always the "latest snapshot".
    """
    exp = experiment_service.get(session, experiment_id)
    if exp.status == ExperimentStatus.DRAFT:
        raise ConflictError(
            "Cannot generate a report for an experiment that has never run",
            details={"experiment_id": experiment_id, "status": exp.status.value},
        )

    existing = (
        session.query(Report)
        .filter(Report.experiment_id == experiment_id)
        .one_or_none()
    )
    if existing is not None:
        existing.summary = summary
        existing.recommendation = recommendation
        existing.business_impact = business_impact
        existing.next_steps = list(next_steps or [])
        existing.details = details
        row = existing
    else:
        row = Report(
            experiment_id=experiment_id,
            summary=summary,
            recommendation=recommendation,
            business_impact=business_impact,
            next_steps=list(next_steps or []),
            details=details,
        )
        session.add(row)

    # Reporting implies the experiment is done — mark completed if it's still
    # RUNNING/VALIDATED. (Auto-stopped or manually stopped experiments keep
    # their existing status.)
    if exp.status in (ExperimentStatus.RUNNING, ExperimentStatus.VALIDATED):
        experiment_service.mark_completed(session, experiment_id)

    session.commit()
    session.refresh(row)
    return row