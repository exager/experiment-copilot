"""Custom exception types for the application.

Each error carries an HTTP status code so the API layer can translate it into
a consistent JSON error response.
"""

from __future__ import annotations


class AppError(Exception):
    """Base exception for all application-level errors."""

    status_code: int = 500
    code: str = "internal_error"

    def __init__(self, message: str, *, details: dict | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def to_dict(self) -> dict:
        return {
            "error": self.code,
            "message": self.message,
            "details": self.details,
        }


class NotFoundError(AppError):
    """Requested resource was not found."""

    status_code = 404
    code = "not_found"


class ValidationError(AppError):
    """Input failed validation."""

    status_code = 422
    code = "validation_error"


class RuleEvaluationError(AppError):
    """Rule engine failed to evaluate a rule."""

    status_code = 500
    code = "rule_evaluation_error"


class LLMError(AppError):
    """Underlying LLM call failed or returned an unparseable response."""

    status_code = 502
    code = "llm_error"


class SimulationError(AppError):
    """Simulation engine failed to produce a tick."""

    status_code = 500
    code = "simulation_error"


class ConflictError(AppError):
    """Operation conflicts with current resource state (e.g. relaunch)."""

    status_code = 409
    code = "conflict"