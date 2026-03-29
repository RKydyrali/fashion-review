from __future__ import annotations

import asyncio
from typing import Protocol

from anyio import from_thread

from app.domain.order_status import OrderStatus
from app.schemas.order import OrderRead
from app.websocket.connection_manager import BRANCH_CHANNEL_PREFIX, PRODUCTION_CHANNEL, USER_CHANNEL_PREFIX, manager
from app.websocket.events import OrderRealtimePayload, RealtimeEvent

PRODUCTION_VISIBLE_STATUSES = {
    OrderStatus.ACCEPTED,
    OrderStatus.IN_PRODUCTION,
    OrderStatus.READY,
    OrderStatus.ESCALATED,
}


class OrderEventPublisher(Protocol):
    def publish_order_created(self, order: OrderRead) -> None: ...

    def publish_order_status_changed(
        self,
        order: OrderRead,
        *,
        previous_status: OrderStatus,
        note: str | None = None,
    ) -> None: ...

    def publish_order_reassigned(
        self,
        order: OrderRead,
        *,
        previous_branch_id: int,
        note: str | None = None,
    ) -> None: ...


class NullOrderEventPublisher:
    def publish_order_created(self, order: OrderRead) -> None:
        return None

    def publish_order_status_changed(
        self,
        order: OrderRead,
        *,
        previous_status: OrderStatus,
        note: str | None = None,
    ) -> None:
        return None

    def publish_order_reassigned(
        self,
        order: OrderRead,
        *,
        previous_branch_id: int,
        note: str | None = None,
    ) -> None:
        return None


class WebSocketOrderEventPublisher:
    def __init__(self) -> None:
        self.manager = manager

    def publish_order_created(self, order: OrderRead) -> None:
        payload = OrderRealtimePayload(
            order_id=order.id,
            client_id=order.client_id,
            branch_id=order.branch_id,
            product_id=order.product_id,
            quantity=order.quantity,
            branch_attempt_count=order.branch_attempt_count,
            current_deadline_at=order.current_deadline_at,
            current_deadline_stage=order.current_deadline_stage,
            cancellation_reason=order.cancellation_reason,
            escalation_reason=order.escalation_reason,
            status=order.status,
        )
        self._publish(
            RealtimeEvent(
                event="order_created",
                channels=[
                    f"{USER_CHANNEL_PREFIX}{order.client_id}",
                    f"{BRANCH_CHANNEL_PREFIX}{order.branch_id}",
                ],
                payload=payload.model_dump(mode="json"),
            )
        )

    def publish_order_status_changed(
        self,
        order: OrderRead,
        *,
        previous_status: OrderStatus,
        note: str | None = None,
    ) -> None:
        channels = [
            f"{USER_CHANNEL_PREFIX}{order.client_id}",
            f"{BRANCH_CHANNEL_PREFIX}{order.branch_id}",
        ]
        if order.status in PRODUCTION_VISIBLE_STATUSES or previous_status in PRODUCTION_VISIBLE_STATUSES:
            channels.append(PRODUCTION_CHANNEL)

        payload = OrderRealtimePayload(
            order_id=order.id,
            client_id=order.client_id,
            branch_id=order.branch_id,
            product_id=order.product_id,
            quantity=order.quantity,
            branch_attempt_count=order.branch_attempt_count,
            current_deadline_at=order.current_deadline_at,
            current_deadline_stage=order.current_deadline_stage,
            cancellation_reason=order.cancellation_reason,
            escalation_reason=order.escalation_reason,
            status=order.status,
            previous_status=previous_status,
            note=note,
        )
        self._publish(
            RealtimeEvent(
                event="order_status_changed",
                channels=channels,
                payload=payload.model_dump(mode="json"),
            )
        )

    def publish_order_reassigned(
        self,
        order: OrderRead,
        *,
        previous_branch_id: int,
        note: str | None = None,
    ) -> None:
        payload = OrderRealtimePayload(
            order_id=order.id,
            client_id=order.client_id,
            branch_id=order.branch_id,
            previous_branch_id=previous_branch_id,
            product_id=order.product_id,
            quantity=order.quantity,
            branch_attempt_count=order.branch_attempt_count,
            current_deadline_at=order.current_deadline_at,
            current_deadline_stage=order.current_deadline_stage,
            cancellation_reason=order.cancellation_reason,
            escalation_reason=order.escalation_reason,
            status=order.status,
            note=note,
        )
        self._publish(
            RealtimeEvent(
                event="order_reassigned",
                channels=list(
                    {
                        f"{USER_CHANNEL_PREFIX}{order.client_id}",
                        f"{BRANCH_CHANNEL_PREFIX}{previous_branch_id}",
                        f"{BRANCH_CHANNEL_PREFIX}{order.branch_id}",
                    }
                ),
                payload=payload.model_dump(mode="json"),
            )
        )

    def _publish(self, event: RealtimeEvent) -> None:
        try:
            from_thread.run(self.manager.publish_event, event)
        except RuntimeError:
            asyncio.run(self.manager.publish_event(event))


realtime_order_event_publisher = WebSocketOrderEventPublisher()
