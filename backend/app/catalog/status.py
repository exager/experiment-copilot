"""Experiment lifecycle status.

Moved out of `app.models.experiment` so the graph, services, API, and prompts
can reference it without pulling in the ORM.
"""

from __future__ import annotations

from enum import StrEnum


class ExperimentStatus(StrEnum):
    """Lifecycle states for an experiment."""

    DRAFT = "draft"
    VALIDATED = "validated"
    RUNNING = "running"
    COMPLETED = "completed"
    STOPPED = "stopped"


STATUSES: tuple[ExperimentStatus, ...] = tuple(ExperimentStatus)