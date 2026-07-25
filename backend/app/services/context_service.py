"""Domain service for `ProductContext`.

Thin wrapper around the ORM — API routes only orchestrate; the service
does the persistence work.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.product_context import ProductContext
from app.schemas.context import ProductContextCreate
from app.utils.errors import NotFoundError


def create(session: Session, payload: ProductContextCreate) -> ProductContext:
    """Persist a new ProductContext and return the ORM instance."""
    row = ProductContext(
        business_goal=payload.business_goal,
        website=payload.website,
        current_flow=payload.current_flow,
        feature=payload.feature.value if payload.feature is not None else None,
        pain_point=payload.pain_point,
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    return row


def get(session: Session, context_id: int) -> ProductContext:
    """Fetch a ProductContext or raise `NotFoundError`."""
    row = session.get(ProductContext, context_id)
    if row is None:
        raise NotFoundError(
            f"ProductContext {context_id} not found",
            details={"context_id": context_id},
        )
    return row