"""`POST /experiments/{id}/validate` — run the rule engine on a draft.

Returns a `ValidationResult` shape with rules_evaluated / rules_matched /
rules_rejected / decision / explanation. The service also persists the
result onto `Experiment.validation` and flips status → VALIDATED.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.api.deps import ExperimentDep, SessionDep
from app.schemas.validation import ValidationResult
from app.services import validation_service

router = APIRouter(prefix="/experiments", tags=["experiments"])


@router.post(
    "/{experiment_id}/validate",
    response_model=ValidationResult,
    summary="Run the rule engine on a draft experiment",
)
def validate_experiment(
    experiment: ExperimentDep,
    session: SessionDep,
) -> ValidationResult:
    return validation_service.validate(session, experiment.id)