"""`POST /experiments/{id}/validate` — run the rule engine on a draft.

Returns a `ValidationResult` shape with rules_evaluated / rules_matched /
rules_rejected / decision / explanation. The service also persists the
result onto `Experiment.validation` and flips status → VALIDATED.

Two paths:
  - No body (or an experiment with no paused graph thread — the manual
    `POST /experiments` path): today's behavior, unchanged —
    `validation_service.validate` runs the rule engine directly against
    whatever `hypothesis`/`configuration` are already persisted.
  - A `HypothesisMetricUpdate` body, for an experiment created via
    `POST /context/{id}/hypothesis`: applies the PM's edited metric
    selection to the hypothesis, patches the paused graph's checkpointed
    state, and resumes it — `experiment_design_agent` then `validation_agent`
    run (each persisting via their own services), pausing again before
    `simulation_node`.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.api.deps import ExperimentDep, SessionDep
from app.graph.builder import (
    get_experiment_snapshot,
    resume_experiment,
    update_experiment_state,
)
from app.schemas.hypothesis_review import HypothesisMetricUpdate
from app.schemas.validation import ValidationResult
from app.services import experiment_service, validation_service

router = APIRouter(prefix="/experiments", tags=["experiments"])


@router.post(
    "/{experiment_id}/validate",
    response_model=ValidationResult,
    summary="Run the rule engine on a draft experiment",
)
def validate_experiment(
    experiment: ExperimentDep,
    session: SessionDep,
    metrics: HypothesisMetricUpdate | None = None,
) -> ValidationResult:
    thread_id = str(experiment.id)
    if metrics is not None and get_experiment_snapshot(thread_id).next:
        updated_hypothesis = metrics.apply(experiment.hypothesis or {})
        experiment_service.update_hypothesis(session, experiment.id, updated_hypothesis)
        update_experiment_state(thread_id, {"hypothesis": updated_hypothesis})
        resume_experiment(thread_id)  # experiment_design_agent -> validation_agent -> pause
        # The agent nodes just persisted via their own DB sessions — `session`
        # (and the `experiment` it already loaded) doesn't know about those
        # writes until refreshed.
        session.refresh(experiment)
        return ValidationResult.model_validate(experiment.validation)
    return validation_service.validate(session, experiment.id)