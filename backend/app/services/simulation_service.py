"""Simulation service — bridge between the API layer and the scheduler.

Handles the lifecycle transitions plus scheduler registration so the API
routes can just call `start(session, experiment_id)` / `stop(...)`.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.catalog.status import ExperimentStatus
from app.simulation.scheduler import SimulationScheduler, get_scheduler
from app.services import experiment_service


def start(
    session: Session,
    experiment_id: int,
    scheduler: SimulationScheduler | None = None,
) -> None:
    """Launch the experiment and register a scheduler job for it."""
    experiment_service.launch(session, experiment_id)
    (scheduler or get_scheduler()).register(experiment_id)


def stop(
    session: Session,
    experiment_id: int,
    scheduler: SimulationScheduler | None = None,
) -> None:
    """Manually halt the experiment and deregister its scheduler job."""
    experiment_service.mark_stopped(session, experiment_id)
    (scheduler or get_scheduler()).deregister(experiment_id)


def is_running(
    experiment_id: int, scheduler: SimulationScheduler | None = None
) -> bool:
    """Return True if the simulator currently has a job for `experiment_id`."""
    return (scheduler or get_scheduler()).is_registered(experiment_id)


def resume_if_running(
    session: Session,
    experiment_id: int,
    scheduler: SimulationScheduler | None = None,
) -> None:
    """Re-register a job on process restart if the experiment is still RUNNING."""
    exp = experiment_service.get(session, experiment_id)
    if exp.status == ExperimentStatus.RUNNING:
        (scheduler or get_scheduler()).register(experiment_id)