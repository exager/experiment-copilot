"""Report ORM model.

Stores the final executive report produced by the Report agent once an
experiment is completed (or explicitly reported on).
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.database.base import Base


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    experiment_id: Mapped[int] = mapped_column(
        ForeignKey("experiments.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    recommendation: Mapped[str] = mapped_column(String(32), nullable=False)
    business_impact: Mapped[str | None] = mapped_column(Text, nullable=True)
    # `next_steps` is always a list (possibly empty) so the API schema can
    # safely rely on a non-null value.
    next_steps: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    details: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    experiment: Mapped["Experiment"] = relationship(  # noqa: F821
        "Experiment", back_populates="report"
    )

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return (
            f"<Report exp={self.experiment_id} "
            f"recommendation={self.recommendation!r}>"
        )