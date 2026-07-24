"""FastAPI application entry point.

Wires configuration, logging, database initialization, and API routers.
Additional wiring (routers, scheduler startup) will be added as those
modules are implemented.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from starlette.requests import Request

from app.config import get_settings
from app.database import init_db
from app.logging_config import configure_logging, get_logger
from app.utils.errors import AppError

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa: ARG001 - FastAPI signature
    """Startup / shutdown hooks."""
    configure_logging()
    settings = get_settings()
    logger.info(
        "Starting Experiment Copilot backend "
        "(llm_enabled=%s, langsmith_enabled=%s)",
        settings.llm_enabled,
        settings.langsmith_enabled,
    )
    init_db()
    yield
    logger.info("Shutting down Experiment Copilot backend")


app = FastAPI(
    title="Experiment Copilot API",
    version="0.1.0",
    description="AI-powered A/B experiment decision-support platform.",
    lifespan=lifespan,
)


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:  # noqa: ARG001
    """Translate AppError into a consistent JSON error response."""
    return JSONResponse(status_code=exc.status_code, content=exc.to_dict())


@app.get("/health", tags=["health"])
def health() -> dict:
    """Health check endpoint."""
    return {"status": "ok"}