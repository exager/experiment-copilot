"""Experiment resource routes.

`POST /experiments`               — create a draft (context_id + hypothesis + configuration).
`GET  /experiments/{id}`          — fetch full experiment row.
`POST /experiments/{id}/launch`   — flip to RUNNING + register simulation job.
`POST /experiments/{id}/stop`     — halt manually.

The `hypothesis` / `configuration` payloads accept whatever the caller provides
(so the LangGraph agents on top can populate them). Rule-driven validation
lives at `POST /experiments/{id}/validate` in `validation.py`.
"""

from __future__ import annotations

from fastapi import APIRouter, status
from pydantic import BaseModel, ConfigDict

from app.api.deps import ExperimentDep, SessionDep
from app.schemas.experiment import (
    ExperimentConfiguration,
    ExperimentOut,
    Hypothesis,
)
from app.services import context_service, experiment_service, simulation_service

router = APIRouter(prefix="/experiments", tags=["experiments"])


class CreateExperimentRequest(BaseModel):
    """Body for `POST /experiments`.

    Both `hypothesis` and `configuration` go through Pydantic + catalog
    validation (invalid metric ids / audiences / traffic splits are rejected).
    """

    context_id: int
    hypothesis: Hypothesis
    configuration: ExperimentConfiguration

    model_config = ConfigDict(extra="forbid")


@router.post(
    "",
    response_model=ExperimentOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a draft experiment",
)
def create_experiment(
    payload: CreateExperimentRequest,
    session: SessionDep,
) -> ExperimentOut:
    # Ensure the parent context exists (404 if not).
    context_service.get(session, payload.context_id)
    row = experiment_service.create_draft(
        session,
        context_id=payload.context_id,
        hypothesis=payload.hypothesis.model_dump(),
        configuration=payload.configuration.model_dump(),
    )
    return ExperimentOut.model_validate(row)


@router.get(
    "/{experiment_id}",
    response_model=ExperimentOut,
    summary="Fetch an experiment by id",
)
def get_experiment_endpoint(experiment: ExperimentDep) -> ExperimentOut:
    return ExperimentOut.model_validate(experiment)


@router.post(
    "/{experiment_id}/launch",
    response_model=ExperimentOut,
    summary="Launch a validated experiment (starts simulation)",
)
def launch_experiment(
    experiment: ExperimentDep,
    session: SessionDep,
) -> ExperimentOut:
    simulation_service.start(session, experiment.id)
    row = experiment_service.get(session, experiment.id)
    return ExperimentOut.model_validate(row)


@router.post(
    "/{experiment_id}/stop",
    response_model=ExperimentOut,
    summary="Manually halt a running experiment",
)
def stop_experiment(
    experiment: ExperimentDep,
    session: SessionDep,
) -> ExperimentOut:
    simulation_service.stop(session, experiment.id)
    row = experiment_service.get(session, experiment.id)
    return ExperimentOut.model_validate(row)