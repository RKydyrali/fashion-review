from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.preorder_batch import PreorderBatch
from app.models.order import Order


class PreorderBatchRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, *, client_id: int, delivery_city: str | None, item_count: int, total_price_minor: int, currency: str) -> PreorderBatch:
        batch = PreorderBatch(
            client_id=client_id,
            delivery_city=delivery_city,
            item_count=item_count,
            total_price_minor=total_price_minor,
            currency=currency,
            status="submitted",
        )
        self.session.add(batch)
        self.session.flush()
        return batch

    def list_for_client(self, client_id: int) -> list[PreorderBatch]:
        statement = (
            select(PreorderBatch)
            .options(selectinload(PreorderBatch.orders).selectinload(Order.events), selectinload(PreorderBatch.orders).selectinload(Order.product))
            .where(PreorderBatch.client_id == client_id)
            .order_by(PreorderBatch.id.desc())
        )
        return list(self.session.scalars(statement).unique())
