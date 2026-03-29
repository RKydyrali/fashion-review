from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.models.bag_item import BagItem
from app.models.product import Product


class BagRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_for_user(self, user_id: int) -> list[BagItem]:
        statement = (
            select(BagItem)
            .options(joinedload(BagItem.product).selectinload(Product.translations))
            .where(BagItem.user_id == user_id)
            .order_by(BagItem.id)
        )
        return list(self.session.scalars(statement).unique())

    def get_by_id_for_user(self, item_id: int, user_id: int) -> BagItem | None:
        statement = (
            select(BagItem)
            .options(joinedload(BagItem.product).selectinload(Product.translations))
            .where(BagItem.id == item_id, BagItem.user_id == user_id)
            .limit(1)
        )
        return self.session.scalar(statement)

    def list_for_user_by_ids(self, user_id: int, item_ids: list[int]) -> list[BagItem]:
        if not item_ids:
            return []
        statement = (
            select(BagItem)
            .options(joinedload(BagItem.product).selectinload(Product.translations))
            .where(BagItem.user_id == user_id, BagItem.id.in_(item_ids))
            .order_by(BagItem.id)
        )
        return list(self.session.scalars(statement).unique())

    def get_by_unique_key(self, *, user_id: int, product_id: int, size_label: str) -> BagItem | None:
        statement = (
            select(BagItem)
            .where(BagItem.user_id == user_id, BagItem.product_id == product_id, BagItem.size_label == size_label)
            .limit(1)
        )
        return self.session.scalar(statement)

    def save(self, item: BagItem) -> BagItem:
        self.session.add(item)
        self.session.flush()
        return item

    def delete(self, item: BagItem) -> None:
        self.session.delete(item)
        self.session.flush()

    def delete_for_user_by_ids(self, user_id: int, item_ids: list[int]) -> None:
        if not item_ids:
            return
        self.session.execute(delete(BagItem).where(BagItem.user_id == user_id, BagItem.id.in_(item_ids)))

    def clear_for_user(self, user_id: int) -> None:
        self.session.execute(delete(BagItem).where(BagItem.user_id == user_id))
