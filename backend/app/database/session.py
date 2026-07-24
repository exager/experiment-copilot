"""SQLAlchemy engine, session factory, and helper functions.

The engine and session factory are stored as module-level singletons but
can be swapped at runtime via `configure_database(url)`. Tests use this to
point at an in-memory SQLite database.

Exports:
  - `engine`         — active SQLAlchemy Engine (lazy, built from settings on first use)
  - `SessionLocal`   — sessionmaker bound to `engine`
  - `configure_database(url)` — rebuild engine + SessionLocal against a new URL
  - `init_db()`      — create all tables
  - `get_db()`       — FastAPI dependency yielding a session with cleanup
"""

from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings
from app.database.base import Base


def _make_engine(url: str) -> Engine:
    """Create an Engine, applying SQLite-specific connect args when needed."""
    connect_args: dict = {}
    if url.startswith("sqlite"):
        # Needed so a single connection can be shared across threads
        # (APScheduler jobs and FastAPI request handlers).
        connect_args["check_same_thread"] = False
    return create_engine(url, connect_args=connect_args, future=True)


# --- Module-level singletons (rebuildable via configure_database) ------------

engine: Engine = _make_engine(get_settings().database_url)
SessionLocal: sessionmaker[Session] = sessionmaker(
    bind=engine, autoflush=False, autocommit=False, expire_on_commit=False
)


def configure_database(url: str) -> Engine:
    """Rebuild the engine + SessionLocal against a new database URL.

    Primarily used by tests to attach an in-memory SQLite database. Returns
    the newly-created engine.
    """
    global engine, SessionLocal
    engine = _make_engine(url)
    SessionLocal.configure(bind=engine)
    return engine


def init_db() -> None:
    """Create all tables. Safe to call multiple times.

    Imports the models module so every ORM class is registered on
    `Base.metadata` before `create_all` runs.
    """
    # Local import avoids a circular import at module load time.
    from app import models  # noqa: F401  (side-effect: registers models)

    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a database session and ensures cleanup."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()