"""API routers.

Each submodule exposes a `router: APIRouter`. `register_routers(app)` mounts
them all onto the FastAPI application.
"""

from fastapi import FastAPI

from app.api import catalog, context, experiment, metrics, report, validation


def register_routers(app: FastAPI) -> None:
    """Attach every API router to the FastAPI app."""
    app.include_router(context.router)
    app.include_router(experiment.router)
    app.include_router(validation.router)
    app.include_router(metrics.router)
    app.include_router(report.router)
    app.include_router(catalog.router)


__all__ = ["register_routers"]