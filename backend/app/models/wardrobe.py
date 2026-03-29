from __future__ import annotations

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class WardrobeItem(TimestampMixin, Base):
    __tablename__ = "wardrobe_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey("products.id"), nullable=False)
    size_label: Mapped[str] = mapped_column(String(16), nullable=False)
    color: Mapped[str | None] = mapped_column(String(32), nullable=True)
    fit_notes: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_from_order: Mapped[bool] = mapped_column(default=False, nullable=False)
    order_id: Mapped[int | None] = mapped_column(Integer, nullable=True)

    user: Mapped["User"] = relationship(back_populates="wardrobe_items")
    product: Mapped["Product"] = relationship(back_populates="wardrobe_items")


class WardrobeOutfit(TimestampMixin, Base):
    __tablename__ = "wardrobe_outfits"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    wardrobe_item_ids: Mapped[str] = mapped_column(String(500), nullable=False)

    user: Mapped["User"] = relationship(back_populates="wardrobe_outfits")


from app.models.product import Product
from app.models.user import User
