"""Metrics service — read helpers around the `metrics` table."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.metrics import Metrics


def latest(session: Session, experiment_id: int) -> Metrics | None:
    """Return the most recent metrics row for an experiment (or None)."""
    return (
        session.query(Metrics)
        .filter(Metrics.experiment_id == experiment_id)
        .order_by(Metrics.timestamp.desc())
        .first()
    )


def series(
    session: Session, experiment_id: int, limit: int = 200
) -> list[Metrics]:
    """Return up to `limit` most recent metrics rows in chronological order."""
    rows = (
        session.query(Metrics)
        .filter(Metrics.experiment_id == experiment_id)
        .order_by(Metrics.timestamp.desc())
        .limit(limit)
        .all()
    )
    # Callers want chronological order for charts.
    rows.reverse()
    return rows


def count(session: Session, experiment_id: int) -> int:
    """Return the number of metrics rows recorded for an experiment."""
    return (
        session.query(Metrics.id)
        .filter(Metrics.experiment_id == experiment_id)
        .count()
    )