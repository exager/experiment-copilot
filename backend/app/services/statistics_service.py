"""Statistics service — computes StatisticsOut from the latest metrics row."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.schemas.metrics import StatisticsOut
from app.services import metrics_service
from app.statistics import compute_statistics_from_row


def snapshot(
    session: Session,
    experiment_id: int,
    *,
    confidence_threshold: float = 0.95,
) -> StatisticsOut:
    """Return the current derived statistics for an experiment.

    If no metrics have been recorded yet, returns a zeroed-out
    `StatisticsOut` with `winner=inconclusive`.
    """
    latest = metrics_service.latest(session, experiment_id)
    if latest is None:
        return StatisticsOut(winner="inconclusive", is_significant=False)
    return compute_statistics_from_row(
        latest, confidence_threshold=confidence_threshold
    )