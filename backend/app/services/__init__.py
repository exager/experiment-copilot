"""Domain services layer.

Each submodule exposes plain functions that take a `Session` as the first
positional argument. API routes and background jobs orchestrate; services
own the persistence + rule/statistic invocations.
"""

from app.services import (
    context_service,
    experiment_service,
    metrics_service,
    recommendation_service,
    report_service,
    simulation_service,
    statistics_service,
    validation_service,
)

__all__ = [
    "context_service",
    "experiment_service",
    "metrics_service",
    "recommendation_service",
    "report_service",
    "simulation_service",
    "statistics_service",
    "validation_service",
]