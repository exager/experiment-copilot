"""
SQLAlchemy declarative base.

NOTE (Developer 4 -> Developer 2): `app.models.*` (already committed) import
`Base` from here, but this module was missing from the repo, which made the
entire `app.schemas` / `app.models` import chain (and therefore the LangGraph)
fail to import. This is a minimal declarative `Base` to unblock everyone. If you
have a richer database setup (engine, session, init_db), extend this file but
keep the `Base` symbol so existing model imports keep working.
"""

from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Declarative base shared by all ORM models."""
