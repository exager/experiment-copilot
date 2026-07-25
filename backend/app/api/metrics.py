"""`GET /experiments/{id}/metrics` — dashboard-shaped snapshot.

Bundles the latest metrics row, a chronological series for charting, the
current derived statistics, and the current recommendation into a single
`MetricsSnapshot` payload the frontend polls every ~5 s.
"""

from __future__ import annotations

from fastapi import APIRouter, Query

from app.api.deps import ExperimentDep, SessionDep
from app.schemas.metrics import MetricPoint, MetricsSnapshot
from app.services import (
    metrics_service,
    recommendation_service,
    statistics_service,
)
from app.simulation.scheduler import _guardrail_regressed

router = APIRouter(prefix="/experiments", tags=["experiments"])


@router.get(
    "/{experiment_id}/metrics",
    response_model=MetricsSnapshot,
    summary="Current metrics snapshot for the dashboard",
)
def get_metrics(
    experiment: ExperimentDep,
    session: SessionDep,
    limit: int = Query(200, ge=1, le=1000),
) -> MetricsSnapshot:
    latest = metrics_service.latest(session, experiment.id)
    series = metrics_service.series(session, experiment.id, limit=limit)
    stats = statistics_service.snapshot(session, experiment.id)

    # Sample-ratio for the recommendation rules.
    sample_size = int((experiment.configuration or {}).get("sample_size") or 0)
    total_users = 0 if latest is None else (latest.users_control + latest.users_variant)
    sample_ratio = min(1.0, total_users / sample_size) if sample_size > 0 else 0.0

    guardrail_regressed = _guardrail_regressed(
        latest.guardrails if latest is not None else None
    )

    recommendation = recommendation_service.recommend(
        stats,
        guardrail_regressed=guardrail_regressed,
        sample_ratio=sample_ratio,
    )

    return MetricsSnapshot(
        experiment_id=experiment.id,
        latest=MetricPoint.model_validate(latest) if latest else None,
        series=[MetricPoint.model_validate(row) for row in series],
        statistics=stats,
        recommendation=recommendation,
    )