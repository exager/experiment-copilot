"""`GET /catalog` — expose all pre-set enums (features / audiences / metrics /
traffic splits / durations / confidence levels / statuses).

Lets any frontend render dropdowns without hard-coding the enum values.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.catalog import catalog_summary

router = APIRouter(tags=["catalog"])


@router.get(
    "/catalog",
    summary="All catalog enums (features / audiences / metrics / options)",
)
def get_catalog() -> dict:
    return catalog_summary()