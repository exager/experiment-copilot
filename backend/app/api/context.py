"""`POST /context` — persist the PM's Home-form input.

Cheap, synchronous, non-AI. Creates one row in `product_contexts` and returns
the persisted representation with its id. Downstream endpoints reference the
context by that id.
"""

from __future__ import annotations

from fastapi import APIRouter, status

from app.api.deps import SessionDep
from app.schemas.context import ProductContextCreate, ProductContextOut
from app.services import context_service

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