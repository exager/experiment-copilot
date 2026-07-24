"""Placeholder simulation/statistics nodes.

These stand in for Developer 2's SimulationService/StatisticsService so the
graph is runnable end-to-end today. Both produce fixed, realistic values
shaped exactly like app.schemas.metrics.MetricPoint/StatisticsOut — swap
these out for the real services once they exist.
"""

from __future__ import annotations

_TODO = "Developer 2: replace with real SimulationService/StatisticsService"


def simulation_node(state: dict) -> dict:
    metrics = {
        "users_control": 1200,
        "users_variant": 1190,
        "conversion_control": 52,  # ~4.32% of users_control
        "conversion_variant": 59,  # ~4.93% of users_variant
        "revenue_control": 542.0,
        "revenue_variant": 616.0,
        "_todo": _TODO,
    }
    return {"metrics": metrics}


def statistics_node(state: dict) -> dict:
    metrics = state.get("metrics") or {}
    users_control = metrics.get("users_control") or 1
    users_variant = metrics.get("users_variant") or 1
    conversion_control = metrics.get("conversion_control") or 0
    conversion_variant = metrics.get("conversion_variant") or 0

    control_rate = conversion_control / users_control
    variant_rate = conversion_variant / users_variant
    lift = (variant_rate - control_rate) / control_rate if control_rate else 0.0

    statistics = {
        "p_value": 0.0008,
        "confidence": 0.963,
        "conversion_lift": round(lift, 4),
        "z_score": 2.9,
        "control_conversion_rate": round(control_rate, 4),
        "variant_conversion_rate": round(variant_rate, 4),
        "winner": "variant" if variant_rate > control_rate else "control",
        "is_significant": True,
        "_todo": _TODO,
    }
    return {"statistics": statistics}
