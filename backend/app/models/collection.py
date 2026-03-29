from __future__ import annotations

from sqlalchemy import Boolean, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class Collection(TimestampMixin, Base):
    __tablename__ = "collections"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    hero_image_url: Mapped[str] = mapped_column(String(500), nullable=False)
    cover_image_url: Mapped[str] = mapped_column(String(500), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")
    is_featured: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="1")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="1")
    name_translations: Mapped[dict[str, str]] = mapped_column(JSON, default=dict, nullable=False)
    summary_translations: Mapped[dict[str, str]] = mapped_column(JSON, default=dict, nullable=False)
    eyebrow_translations: Mapped[dict[str, str]] = mapped_column(JSON, default=dict, nullable=False)
