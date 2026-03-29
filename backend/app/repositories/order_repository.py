from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.domain.order_deadline_stage import OrderDeadlineStage
from app.domain.order_status import OrderStatus
from app.models.order import Order
from app.schemas.order import OrderCreate


class OrderRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(
        self,
        payload: OrderCreate,
        *,
        client_id: int,
        branch_id: int,
        delivery_city: str | None,
        branch_attempt_count: int,
        current_deadline_at: datetime | None = None,
        current_deadline_stage: OrderDeadlineStage | None = None,
    ) -> Order:
        order = Order(
            client_id=client_id,
            product_id=payload.product_id,
            branch_id=branch_id,
            preorder_batch_id=payload.preorder_batch_id,
            delivery_city=delivery_city,
            size_label=payload.size_label,
            quantity=payload.quantity,
            unit_price_minor=0,
            tailoring_adjustment_minor=0,
            total_price_minor=0,
            currency="USD",
            branch_attempt_count=branch_attempt_count,
            current_deadline_at=current_deadline_at,
            current_deadline_stage=current_deadline_stage,
            status=OrderStatus.CREATED,
        )
        self.session.add(order)
        self.session.flush()
        return order

    def get_by_id(self, order_id: int) -> Order | None:
        statement = (
            select(Order)
            .options(selectinload(Order.events), selectinload(Order.product))
            .where(Order.id == order_id)
        )
        return self.session.scalar(statement)

    def list_for_client(self, client_id: int) -> list[Order]:
        statement = (
            select(Order)
            .options(selectinload(Order.events), selectinload(Order.product))
            .where(Order.client_id == client_id)
            .order_by(Order.id)
        )
        return list(self.session.scalars(statement))

    def list_for_branch(self, branch_id: int) -> list[Order]:
        statement = (
            select(Order)
            .options(selectinload(Order.events), selectinload(Order.product))
            .where(Order.branch_id == branch_id)
            .order_by(Order.id)
        )
        return list(self.session.scalars(statement))

    def list_by_statuses(self, statuses: tuple[OrderStatus, ...]) -> list[Order]:
        statement = (
            select(Order)
            .options(selectinload(Order.events), selectinload(Order.product))
            .where(Order.status.in_(statuses))
            .order_by(Order.id)
        )
        return list(self.session.scalars(statement))

    def list_due_for_sla(self, *, now: datetime, statuses: tuple[OrderStatus, ...]) -> list[Order]:
        statement = (
            select(Order)
            .options(selectinload(Order.events), selectinload(Order.product))
            .where(
                Order.status.in_(statuses),
                Order.current_deadline_at.is_not(None),
                Order.current_deadline_at <= now,
            )
            .order_by(Order.id)
        )
        return list(self.session.scalars(statement))

    def save(self, order: Order) -> Order:
        self.session.add(order)
        self.session.flush()
        return order
