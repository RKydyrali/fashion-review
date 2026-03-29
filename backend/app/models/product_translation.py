from __future__ import annotations

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class ProductTranslation(Base):
    __tablename__ = "product_translations"

    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), primary_key=True)
    language_code: Mapped[str] = mapped_column(String(2), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    subtitle: Mapped[str | None] = mapped_column(String(255), nullable=True)
    long_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    fabric_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    care_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    preorder_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    display_category: Mapped[str] = mapped_column(String(100), nullable=False)

    product: Mapped["Product"] = relationship(back_populates="translations")
