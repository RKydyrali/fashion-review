from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.order_deadline_stage import OrderDeadlineStage
from app.domain.order_status import OrderStatus
from app.models.base import Base, TimestampMixin


class Order(TimestampMixin, Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    branch_id: Mapped[int] = mapped_column(ForeignKey("branches.id"), index=True, nullable=False)
    preorder_batch_id: Mapped[int | None] = mapped_column(ForeignKey("preorder_batches.id"), index=True, nullable=True)
    delivery_city: Mapped[str | None] = mapped_column(String(120), nullable=True)
    size_label: Mapped[str | None] = mapped_column(String(16), nullable=True)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price_minor: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    tailoring_adjustment_minor: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    total_price_minor: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD", server_default="USD")
    branch_attempt_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        server_default="1",
    )
    current_deadline_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    current_deadline_stage: Mapped[OrderDeadlineStage | None] = mapped_column(
        Enum(OrderDeadlineStage, name="order_deadline_stage", native_enum=False),
        nullable=True,
        index=True,
    )
    cancellation_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    escalation_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[OrderStatus] = mapped_column(
        Enum(OrderStatus, name="order_status", native_enum=False),
        index=True,
        nullable=False,
        default=OrderStatus.CREATED,
        server_default=OrderStatus.CREATED.value,
    )

    client: Mapped["User"] = relationship(
        back_populates="client_orders",
        foreign_keys=[client_id],
    )
    preorder_batch: Mapped["PreorderBatch | None"] = relationship(back_populates="orders")
    product: Mapped["Product"] = relationship(back_populates="orders")
    branch: Mapped["Branch"] = relationship(back_populates="orders")
    events: Mapped[list["OrderEvent"]] = relationship(
        back_populates="order",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="OrderEvent.id",
    )
