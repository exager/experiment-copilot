"""`POST /context` — persist the PM's Home-form input.

Cheap, synchronous, non-AI. Creates one row in `product_contexts` and returns
the persisted representation with its id. Downstream endpoints reference the
context by that id.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Path, status

from app.api.deps import SessionDep
from app.schemas.context import ProductContextCreate, ProductContextOut
from app.schemas.hypothesis_review import HypothesisReview
from app.services import context_service, hypothesis_service

router = APIRouter(tags=["context"])


@router.post(
    "/context",
    response_model=ProductContextOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a Product Context",
    description=(
        "Persist the PM-entered product context (business goal, website, current "
        "flow, feature, pain point). Returns the stored record with its id, which "
        "downstream endpoints reference to generate hypotheses and experiments."
    ),
)
def create_context(
    payload: ProductContextCreate,
    session: SessionDep,
) -> ProductContextOut:
    row = context_service.create(session, payload)
    return ProductContextOut.model_validate(row)


@router.post(
    "/context/{context_id}/hypothesis",
    response_model=HypothesisReview,
    summary="Generate a hypothesis for review (context -> hypothesis, then pause)",
    description=(
        "Runs the AI pipeline (context_agent -> hypothesis_agent) for the given "
        "context and pauses at the human-in-the-loop interrupt. Returns the AI "
        "problem statement plus, for each metric role, the full catalog of "
        "eligible metrics with a `selected` flag marking the AI's picks, so the "
        "user can review and adjust before launching."
    ),
)
def generate_hypothesis(
    context_id: Annotated[int, Path(..., ge=1)],
    session: SessionDep,
) -> HypothesisReview:
    return hypothesis_service.generate_review(session, context_id)