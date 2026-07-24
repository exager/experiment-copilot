"""Metrics ORM model.

Each row is a snapshot of experiment metrics at a point in time. The
simulation engine appends one row per tick (every 5 seconds by default).
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class Metrics(Base):
    __tablename__ = "metrics"
    __table_args__ = (
        Index("ix_metrics_experiment_timestamp", "experiment_id", "timestamp"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    experiment_id: Mapped[int] = mapped_column(
        ForeignKey("experiments.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Cumulative counts per arm.
    users_control: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    users_variant: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    conversion_control: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    conversion_variant: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    revenue_control: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0
    )
    revenue_variant: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0
    )

    # Derived statistics stored for fast retrieval by the dashboard.
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    p_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    conversion_lift: Mapped[float | None] = mapped_column(Float, nullable=True)

    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    experiment: Mapped["Experiment"] = relationship(  # noqa: F821
        "Experiment", back_populates="metrics"
    )

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return (
            f"<Metrics exp={self.experiment_id} "
            f"users(c/v)={self.users_control}/{self.users_variant} "
            f"conf={self.confidence}>"
        )