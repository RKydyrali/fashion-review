from __future__ import annotations

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Branch(TimestampMixin, Base):
    __tablename__ = "branches"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    city: Mapped[str] = mapped_column(String(120), nullable=False)
    manager_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)

    manager: Mapped["User"] = relationship(
        back_populates="managed_branches",
        foreign_keys=[manager_user_id],
    )
    orders: Mapped[list["Order"]] = relationship(back_populates="branch")
