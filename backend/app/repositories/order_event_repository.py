from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.order_event_type import OrderEventType
from app.domain.order_status import OrderStatus
from app.models.order_event import OrderEvent


class OrderEventRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(
        self,
        *,
        order_id: int,
        actor_user_id: int | None,
        event_type: OrderEventType,
        from_status: OrderStatus | None,
        to_status: OrderStatus,
        note: str | None = None,
        metadata: dict[str, object] | None = None,
    ) -> OrderEvent:
        event = OrderEvent(
            order_id=order_id,
            actor_user_id=actor_user_id,
            event_type=event_type,
            from_status=from_status,
            to_status=to_status,
            note=note,
            event_metadata=metadata,
        )
        self.session.add(event)
        self.session.flush()
        return event

    def list_for_order(self, order_id: int) -> list[OrderEvent]:
        statement = select(OrderEvent).where(OrderEvent.order_id == order_id).order_by(OrderEvent.id)
        return list(self.session.scalars(statement))
