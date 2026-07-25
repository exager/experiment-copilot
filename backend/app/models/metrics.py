"""Metrics ORM model.

Each row is a snapshot of experiment metrics at a point in time. The
simulation engine appends one row per tick (every 5 seconds by default),
carrying cumulative counts per arm plus derived statistics and the current
recommendation.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

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
    # Cumulative bounce (guardrail) events per arm.
    bounce_events_control: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    bounce_events_variant: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )

    # Per-guardrail-metric snapshot for this tick (id → {control, variant}).
    # Example: {"page_load_time_ms": {"control": 1180, "variant": 1210}, ...}
    guardrails: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Derived statistics stored for fast retrieval by the dashboard.
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    p_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    conversion_lift: Mapped[float | None] = mapped_column(Float, nullable=True)
    z_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    winner: Mapped[str | None] = mapped_column(String(16), nullable=True)

    # Recommendation snapshot (from the rule engine).
    recommendation: Mapped[str | None] = mapped_column(String(32), nullable=True)
    recommendation_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

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
            f"winner={self.winner} rec={self.recommendation}>"
        )