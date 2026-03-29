from __future__ import annotations

from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class BagItem(TimestampMixin, Base):
    __tablename__ = "bag_items"
    __table_args__ = (UniqueConstraint("user_id", "product_id", "size_label", name="uq_bag_user_product_size"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), index=True, nullable=False)
    size_label: Mapped[str] = mapped_column(String(16), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")
    unit_price_minor: Mapped[int] = mapped_column(Integer, nullable=False)
    adjustment_minor: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    line_total_minor: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD", server_default="USD")

    user: Mapped["User"] = relationship(back_populates="bag_items")
    product: Mapped["Product"] = relationship(back_populates="bag_items")
