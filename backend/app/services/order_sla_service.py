from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.domain.order_status import OrderStatus
from app.schemas.order import OrderRead
from app.services.order_service import OrderService


class OrderSLAService:
    def __init__(self, session: Session, order_service: OrderService | None = None) -> None:
        self.session = session
        self.order_service = order_service or OrderService(session)

    def run_due_actions(self, *, now: datetime | None = None) -> list[OrderRead]:
        effective_now = (now or datetime.now(timezone.utc)).astimezone(timezone.utc).replace(tzinfo=None)
        due_orders = self.order_service.orders.list_due_for_sla(
            now=effective_now,
            statuses=(OrderStatus.CREATED, OrderStatus.ACCEPTED, OrderStatus.IN_PRODUCTION),
        )
        updated_orders: list[OrderRead] = []
        for due_order in due_orders:
            updated = self.order_service.process_sla_expiration(due_order.id, now=effective_now)
            if updated is not None:
                updated_orders.append(updated)
        return updated_orders
