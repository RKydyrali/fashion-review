from __future__ import annotations

from sqlalchemy import Boolean, Enum, Float, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.language import DEFAULT_LANGUAGE
from app.domain.roles import UserRole
from app.models.base import Base, TimestampMixin


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(255))
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role", native_enum=False),
        index=True,
        nullable=False,
    )
    preferred_language: Mapped[str] = mapped_column(
        String(2),
        nullable=False,
        default=DEFAULT_LANGUAGE.value,
        server_default=DEFAULT_LANGUAGE.value,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="1", nullable=False)
    height_cm: Mapped[float | None] = mapped_column(Float, nullable=True)
    weight_kg: Mapped[float | None] = mapped_column(Float, nullable=True)
    chest_cm: Mapped[float | None] = mapped_column(Float, nullable=True)
    waist_cm: Mapped[float | None] = mapped_column(Float, nullable=True)
    hips_cm: Mapped[float | None] = mapped_column(Float, nullable=True)
    preferred_fit: Mapped[str | None] = mapped_column(String(16), nullable=True)
    alpha_size: Mapped[str | None] = mapped_column(String(32), nullable=True)
    top_size: Mapped[str | None] = mapped_column(String(32), nullable=True)
    bottom_size: Mapped[str | None] = mapped_column(String(32), nullable=True)
    dress_size: Mapped[str | None] = mapped_column(String(32), nullable=True)
    first_order_discount_used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    client_orders: Mapped[list["Order"]] = relationship(
        back_populates="client",
        foreign_keys="Order.client_id",
    )
    managed_branches: Mapped[list["Branch"]] = relationship(
        back_populates="manager",
        foreign_keys="Branch.manager_user_id",
    )
    order_events: Mapped[list["OrderEvent"]] = relationship(
        back_populates="actor",
        foreign_keys="OrderEvent.actor_user_id",
    )
    favorites: Mapped[list["Favorite"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    bag_items: Mapped[list["BagItem"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    preorder_batches: Mapped[list["PreorderBatch"]] = relationship(
        back_populates="client",
        foreign_keys="PreorderBatch.client_id",
    )
    refresh_sessions: Mapped[list["RefreshSession"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    wardrobe_items: Mapped[list["WardrobeItem"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    wardrobe_outfits: Mapped[list["WardrobeOutfit"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )


from app.models.wardrobe import WardrobeItem, WardrobeOutfit  # noqa: E402
