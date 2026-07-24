"""Domain service for the `Experiment` lifecycle.

Every state transition (draft → validated → running → completed/stopped)
lives here so routes and the scheduler share a single source of truth.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.catalog.status import ExperimentStatus
from app.models.experiment import Experiment
from app.utils.errors import ConflictError, NotFoundError


def create_draft(
    session: Session,
    *,
    context_id: int,
    hypothesis: dict,
    configuration: dict,
) -> Experiment:
    """Create a new experiment in DRAFT with the given AI-generated blobs."""
    row = Experiment(
        context_id=context_id,
        hypothesis=hypothesis or {},
        configuration=configuration or {},
        status=ExperimentStatus.DRAFT,
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    return row


def get(session: Session, experiment_id: int) -> Experiment:
    row = session.get(Experiment, experiment_id)
    if row is None:
        raise NotFoundError(
            f"Experiment {experiment_id} not found",
            details={"experiment_id": experiment_id},
        )
    return row


def update_configuration(
    session: Session, experiment_id: int, configuration: dict
) -> Experiment:
    """Overwrite the configuration blob (used when the PM edits before launch)."""
    exp = get(session, experiment_id)
    if exp.status not in (ExperimentStatus.DRAFT, ExperimentStatus.VALIDATED):
        raise ConflictError(
            f"Cannot edit configuration when experiment is {exp.status.value}",
            details={"experiment_id": experiment_id, "status": exp.status.value},
        )
    exp.configuration = configuration
    # Editing invalidates a prior validation pass.
    if exp.status == ExperimentStatus.VALIDATED:
        exp.status = ExperimentStatus.DRAFT
        exp.validation = None
    session.commit()
    session.refresh(exp)
    return exp


def mark_validated(
    session: Session, experiment_id: int, validation: dict
) -> Experiment:
    """Persist the validation blob and flip status to VALIDATED."""
    exp = get(session, experiment_id)
    if exp.status not in (ExperimentStatus.DRAFT, ExperimentStatus.VALIDATED):
        raise ConflictError(
            f"Cannot validate an experiment in state {exp.status.value}",
            details={"experiment_id": experiment_id, "status": exp.status.value},
        )
    exp.validation = validation
    exp.status = ExperimentStatus.VALIDATED
    session.commit()
    session.refresh(exp)
    return exp


def launch(session: Session, experiment_id: int) -> Experiment:
    """Move from VALIDATED → RUNNING. Records `started_at`.

    Raises ConflictError if the experiment isn't yet validated.
    """
    exp = get(session, experiment_id)
    if exp.status == ExperimentStatus.RUNNING:
        return exp  # idempotent
    if exp.status != ExperimentStatus.VALIDATED:
        raise ConflictError(
            f"Cannot launch experiment in state {exp.status.value}; "
            f"expected VALIDATED",
            details={"experiment_id": experiment_id, "status": exp.status.value},
        )
    exp.status = ExperimentStatus.RUNNING
    exp.started_at = datetime.now(tz=timezone.utc)
    session.commit()
    session.refresh(exp)
    return exp


def mark_completed(session: Session, experiment_id: int) -> Experiment:
    """Set status → COMPLETED and stamp `completed_at`."""
    exp = get(session, experiment_id)
    if exp.status == ExperimentStatus.COMPLETED:
        return exp
    exp.status = ExperimentStatus.COMPLETED
    exp.completed_at = datetime.now(tz=timezone.utc)
    session.commit()
    session.refresh(exp)
    return exp


def mark_stopped(session: Session, experiment_id: int) -> Experiment:
    """Set status → STOPPED (manual halt) and stamp `completed_at`."""
    exp = get(session, experiment_id)
    if exp.status in (ExperimentStatus.COMPLETED, ExperimentStatus.STOPPED):
        return exp
    exp.status = ExperimentStatus.STOPPED
    exp.completed_at = datetime.now(tz=timezone.utc)
    session.commit()
    session.refresh(exp)
    return exp