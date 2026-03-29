from __future__ import annotations

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class PreorderBatch(TimestampMixin, Base):
    __tablename__ = "preorder_batches"

    id: Mapped[int] = mapped_column(primary_key=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    delivery_city: Mapped[str | None] = mapped_column(String(120), nullable=True)
    item_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    total_price_minor: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD", server_default="USD")
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="submitted", server_default="submitted")

    client: Mapped["User"] = relationship(back_populates="preorder_batches")
    orders: Mapped[list["Order"]] = relationship(back_populates="preorder_batch")
