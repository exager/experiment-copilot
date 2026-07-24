"""ProductContext ORM model.

Captures the raw product information a PM enters on the Home page. This is
the input that seeds the entire experiment lifecycle.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class ProductContext(Base):
    __tablename__ = "product_contexts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    business_goal: Mapped[str] = mapped_column(Text, nullable=False)
    website: Mapped[str | None] = mapped_column(String(512), nullable=True)
    current_flow: Mapped[str | None] = mapped_column(Text, nullable=True)
    feature: Mapped[str | None] = mapped_column(String(256), nullable=True)
    pain_point: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    experiments: Mapped[list["Experiment"]] = relationship(  # noqa: F821
        "Experiment",
        back_populates="context",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<ProductContext id={self.id} goal={self.business_goal[:30]!r}>"