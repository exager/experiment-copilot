"""Shared DB-session helper for graph nodes that persist via the services.

Nodes only persist when `experiment_id` is present in state — absent for the
standalone unit tests in `tests/test_agents.py`, which call `.node(state)`
directly with hand-built dicts and no DB behind them (see
`app/graph/state.py`).
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

from sqlalchemy.orm import Session

from app.database import SessionLocal


@contextmanager
def maybe_session(state: dict) -> Iterator[Session | None]:
    """Yield an open `Session` if `state["experiment_id"]` is set, else `None`."""
    if state.get("experiment_id") is None:
        yield None
        return
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
