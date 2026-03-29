from __future__ import annotations

from typing import Any
from typing import TYPE_CHECKING

from sqlalchemy import JSON, Enum, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.order_event_type import OrderEventType
from app.domain.order_status import OrderStatus
from app.models.base import Base, CreatedAtMixin

if TYPE_CHECKING:
    from app.models.order import Order
    from app.models.user import User


class OrderEvent(CreatedAtMixin, Base):
    __tablename__ = "order_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"), index=True, nullable=False)
    actor_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    event_type: Mapped[OrderEventType] = mapped_column(
        Enum(OrderEventType, name="order_event_type", native_enum=False),
        nullable=False,
    )
    from_status: Mapped[OrderStatus | None] = mapped_column(
        Enum(OrderStatus, name="order_event_from_status", native_enum=False),
        nullable=True,
    )
    to_status: Mapped[OrderStatus] = mapped_column(
        Enum(OrderStatus, name="order_event_to_status", native_enum=False),
        nullable=False,
    )
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    event_metadata: Mapped[dict[str, Any] | None] = mapped_column("metadata", JSON, nullable=True)

    order: Mapped[Order] = relationship(back_populates="events")
    actor: Mapped[User | None] = relationship(
        back_populates="order_events",
        foreign_keys=[actor_user_id],
    )
