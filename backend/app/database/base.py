
"""SQLAlchemy declarative Base.

Kept in its own module so ORM models can import Base without creating an
import cycle with `session.py`.
"""


from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""
