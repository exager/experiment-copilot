"""Simulation/statistics nodes.

These run the *real*, persisted simulation: `app.simulation.scheduler.run_one_tick`
(the same tick logic the live 5-second scheduler uses) is looped
synchronously, inside a single graph resume, until the experiment's
configured sample size is reached — real `Metrics` rows land in the DB just
like a live-ticking experiment would, just without waiting on wall-clock
time between ticks.

Requires `experiment_id` in state (always present on this path — these two
nodes only ever run after `POST /experiments/{id}/launch` has resumed a
persisted, graph-driven experiment).
"""

from __future__ import annotations

from app.database import SessionLocal
from app.models.metrics import Metrics
from app.services import metrics_service, statistics_service
from app.simulation.scheduler import _guardrail_regressed, run_one_tick

_MAX_TICKS = 500  # covers the largest catalog sample size with headroom


def _metrics_row_to_dict(row: Metrics) -> dict:
    return {
        "users_control": row.users_control,
        "users_variant": row.users_variant,
        "conversion_control": row.conversion_control,
        "conversion_variant": row.conversion_variant,
        "revenue_control": row.revenue_control,
        "revenue_variant": row.revenue_variant,
        "bounce_events_control": row.bounce_events_control,
        "bounce_events_variant": row.bounce_events_variant,
        "guardrails": row.guardrails,
    }


def simulation_node(state: dict) -> dict:
    experiment_id = state["experiment_id"]

    completed = False

    def _mark_complete(_experiment_id: int) -> None:
        nonlocal completed
        completed = True

    ticks = 0
    while not completed and ticks < _MAX_TICKS:
        run_one_tick(SessionLocal, experiment_id, on_complete=_mark_complete)
        ticks += 1

    session = SessionLocal()
    try:
        latest = metrics_service.latest(session, experiment_id)
        metrics = _metrics_row_to_dict(latest) if latest is not None else {}
    finally:
        session.close()

    return {"metrics": metrics}


def statistics_node(state: dict) -> dict:
    experiment_id = state["experiment_id"]
    configuration = state.get("configuration") or {}

    session = SessionLocal()
    try:
        stats = statistics_service.snapshot(session, experiment_id).model_dump()
        latest = metrics_service.latest(session, experiment_id)
    finally:
        session.close()

    # The recommendation rule engine reads these two fields to decide
    # "rollback" and "stop_when_sample_exhausted" — without them it can only
    # ever reach scale/stop/continue (see recommendation_rules.json).
    sample_size = configuration.get("sample_size") or 0
    total_users = 0 if latest is None else latest.users_control + latest.users_variant
    stats["sample_ratio"] = min(1.0, total_users / sample_size) if sample_size else 0.0
    stats["guardrail_regression"] = _guardrail_regressed(
        latest.guardrails if latest is not None else None
    )

    return {"statistics": stats}
