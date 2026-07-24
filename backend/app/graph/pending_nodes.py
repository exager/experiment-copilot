"""Simulation/statistics nodes.

These run the real synthetic-metrics generator (`app.simulation.generator`)
and the real statistics engine (`app.statistics.engine`) inline, one-shot,
to take the graph from a validated configuration straight to a finished
metrics snapshot — enough to demo the full pipeline without a running
scheduler or database.

This is deliberately NOT the live "every 5 seconds" experiment: that's
`app.simulation.scheduler`, which ticks a *persisted* Experiment over real
time and writes `Metrics` rows via the (still-to-be-built) API/service
layer. Here there is no experiment id yet — the graph runs ahead of
persistence — so ticks are seeded off a fixed id and replayed in a loop
until the configured sample size is reached (or a safety cap is hit).
"""

from __future__ import annotations

from app.simulation.generator import TickSnapshot, apply_delta, inputs_from_experiment, next_tick
from app.statistics import compute_statistics

_SEED_EXPERIMENT_ID = 0
_MAX_TICKS = 500  # covers the largest catalog sample size with headroom


def simulation_node(state: dict) -> dict:
    hypothesis = state.get("hypothesis") or {}
    configuration = state.get("configuration") or {}
    inputs = inputs_from_experiment(
        _SEED_EXPERIMENT_ID, hypothesis=hypothesis, configuration=configuration
    )

    snapshot = TickSnapshot.zero()
    tick_index = 0
    total_users = 0
    while total_users < inputs.sample_size and tick_index < _MAX_TICKS:
        delta = next_tick(snapshot, inputs, tick_index)
        snapshot = apply_delta(snapshot, delta)
        total_users = snapshot.users_control + snapshot.users_variant
        tick_index += 1

    metrics = {
        "users_control": snapshot.users_control,
        "users_variant": snapshot.users_variant,
        "conversion_control": snapshot.conversion_control,
        "conversion_variant": snapshot.conversion_variant,
        "revenue_control": snapshot.revenue_control,
        "revenue_variant": snapshot.revenue_variant,
        "bounce_events_control": snapshot.bounce_events_control,
        "bounce_events_variant": snapshot.bounce_events_variant,
        "guardrails": snapshot.guardrails,
    }
    return {"metrics": metrics}


def statistics_node(state: dict) -> dict:
    metrics = state.get("metrics") or {}
    statistics = compute_statistics(
        users_control=metrics.get("users_control") or 0,
        users_variant=metrics.get("users_variant") or 0,
        conversion_control=metrics.get("conversion_control") or 0,
        conversion_variant=metrics.get("conversion_variant") or 0,
    )
    return {"statistics": statistics.model_dump()}
