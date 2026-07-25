"""FastAPI application entry point.

Wires configuration, logging, database initialization, background simulation
scheduler, and every API router.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.requests import Request

from app.api import register_routers
from app.catalog.status import ExperimentStatus
from app.config import get_settings
from app.database import SessionLocal, init_db
from app.logging_config import configure_logging, get_logger
from app.simulation.scheduler import get_scheduler
from app.utils.errors import AppError

logger = get_logger(__name__)


def _resume_running_experiments() -> None:
    """Re-register scheduler jobs for any experiments still in RUNNING state.

    Called on startup so a process restart doesn't leave running experiments
    orphaned without a tick job.
    """
    scheduler = get_scheduler()
    session = SessionLocal()
    try:
        # Local import avoids ORM registration issues on cold start.
        from app.models.experiment import Experiment

        running = (
            session.query(Experiment)
            .filter(Experiment.status == ExperimentStatus.RUNNING)
            .all()
        )
        for exp in running:
            scheduler.register(exp.id)
        if running:
            logger.info("Resumed %d running experiment(s)", len(running))
    finally:
        session.close()


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

    scheduler = get_scheduler()
    scheduler.start()
    try:
        _resume_running_experiments()
    except Exception:  # pragma: no cover - defensive
        logger.exception("Failed to resume running experiments on startup")

    yield

    logger.info("Shutting down Experiment Copilot backend")
    scheduler.shutdown(wait=False)


app = FastAPI(
    title="Experiment Copilot API",
    version="0.1.0",
    description="AI-powered A/B experiment decision-support platform.",
    lifespan=lifespan,
)


# --- Middleware (CORS + trusted hosts) -------------------------------------
# Wide-open by default so the frontend can hit the API from any origin during
# development. Restrict via `CORS_ORIGINS` / `ALLOWED_HOSTS` env vars in prod.
_settings = get_settings()
_wildcard_origins = _settings.cors_origins == ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_settings.cors_origins,
    # The CORS spec forbids `allow_credentials=True` together with a wildcard
    # origin, so we flip it off when origins is ["*"].
    allow_credentials=not _wildcard_origins,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=_settings.allowed_hosts,
)


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:  # noqa: ARG001
    """Translate AppError into a consistent JSON error response."""
    return JSONResponse(status_code=exc.status_code, content=exc.to_dict())


@app.get("/health", tags=["health"])
def health() -> dict:
    """Health check endpoint."""
    return {"status": "ok"}


register_routers(app)