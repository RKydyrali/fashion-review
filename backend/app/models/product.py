from __future__ import annotations

from sqlalchemy import JSON, Boolean, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Product(TimestampMixin, Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    sku: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    slug: Mapped[str] = mapped_column(String(160), unique=True, index=True, nullable=False, default="")
    name: Mapped[str] = mapped_column(String(255), index=True)
    display_category: Mapped[str] = mapped_column(String(100))
    normalized_category: Mapped[str] = mapped_column(String(20), index=True)
    season_tags: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    color: Mapped[str] = mapped_column(String(50))
    subtitle: Mapped[str | None] = mapped_column(String(255), nullable=True)
    long_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    base_price_minor: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD", server_default="USD")
    collection_slug: Mapped[str | None] = mapped_column(String(120), index=True, nullable=True)
    hero_image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    gallery_image_urls: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    fabric_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    care_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    preorder_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    available_sizes: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    size_chart_id: Mapped[int | None] = mapped_column(nullable=True, index=True)
    editorial_rank: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0", nullable=False)
    reference_image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True, server_default="1", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="1", nullable=False)

    translations: Mapped[list["ProductTranslation"]] = relationship(
        back_populates="product",
        cascade="all, delete-orphan",
    )
    orders: Mapped[list["Order"]] = relationship(back_populates="product")
    favorites: Mapped[list["Favorite"]] = relationship(back_populates="product")
    bag_items: Mapped[list["BagItem"]] = relationship(back_populates="product")
    wardrobe_items: Mapped[list["WardrobeItem"]] = relationship(back_populates="product")


from app.models.wardrobe import WardrobeItem  # noqa: E402
