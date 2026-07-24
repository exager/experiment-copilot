"""Experiment ORM model.

Stores the AI-generated hypothesis + configuration plus lifecycle state.
`hypothesis` and `configuration` are stored as JSON blobs so we can evolve
their shapes without a schema migration.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.catalog.status import ExperimentStatus  # re-exported below for back-compat
from app.database.base import Base

__all__ = ["Experiment", "ExperimentStatus"]


class Experiment(Base):
    __tablename__ = "experiments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    context_id: Mapped[int] = mapped_column(
        ForeignKey("product_contexts.id", ondelete="CASCADE"), nullable=False
    )
    hypothesis: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    configuration: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    validation: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    status: Mapped[ExperimentStatus] = mapped_column(
        Enum(ExperimentStatus, name="experiment_status"),
        nullable=False,
        default=ExperimentStatus.DRAFT,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    context: Mapped["ProductContext"] = relationship(  # noqa: F821
        "ProductContext", back_populates="experiments"
    )
    metrics: Mapped[list["Metrics"]] = relationship(  # noqa: F821
        "Metrics",
        back_populates="experiment",
        cascade="all, delete-orphan",
        order_by="Metrics.timestamp",
    )
    report: Mapped[Optional["Report"]] = relationship(  # noqa: F821
        "Report",
        back_populates="experiment",
        cascade="all, delete-orphan",
        uselist=False,
    )

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<Experiment id={self.id} status={self.status.value}>"