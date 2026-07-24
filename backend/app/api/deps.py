"""Shared FastAPI dependencies."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Path
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.experiment import Experiment
from app.services import experiment_service


SessionDep = Annotated[Session, Depends(get_db)]


def get_experiment(
    experiment_id: Annotated[int, Path(..., ge=1)],
    session: SessionDep,
) -> Experiment:
    """Resolve an `experiment_id` path parameter to an ORM row.

    Raises 404 via `NotFoundError` if the experiment doesn't exist.
    """
    return experiment_service.get(session, experiment_id)


ExperimentDep = Annotated[Experiment, Depends(get_experiment)]