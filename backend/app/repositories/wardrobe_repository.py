from __future__ import annotations

import json
from sqlalchemy import delete, select
from sqlalchemy.orm import Session, joinedload

from app.models.wardrobe import WardrobeItem, WardrobeOutfit
from app.models.product import Product


class WardrobeRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_items_for_user(self, user_id: int) -> list[WardrobeItem]:
        statement = (
            select(WardrobeItem)
            .options(joinedload(WardrobeItem.product))
            .where(WardrobeItem.user_id == user_id)
            .order_by(WardrobeItem.id)
        )
        return list(self.session.scalars(statement).unique())

    def get_item_by_id(self, item_id: int, user_id: int) -> WardrobeItem | None:
        statement = (
            select(WardrobeItem)
            .options(joinedload(WardrobeItem.product))
            .where(WardrobeItem.id == item_id, WardrobeItem.user_id == user_id)
            .limit(1)
        )
        return self.session.scalar(statement)

    def get_by_user_and_product(self, user_id: int, product_id: int) -> WardrobeItem | None:
        statement = (
            select(WardrobeItem)
            .where(WardrobeItem.user_id == user_id, WardrobeItem.product_id == product_id)
            .limit(1)
        )
        return self.session.scalar(statement)

    def create_item(
        self,
        user_id: int,
        product_id: int,
        size_label: str,
        color: str | None = None,
        fit_notes: str | None = None,
        is_from_order: bool = False,
        order_id: int | None = None,
    ) -> WardrobeItem:
        item = WardrobeItem(
            user_id=user_id,
            product_id=product_id,
            size_label=size_label,
            color=color,
            fit_notes=fit_notes,
            is_from_order=is_from_order,
            order_id=order_id,
        )
        self.session.add(item)
        self.session.flush()
        return item

    def update_item(
        self,
        item: WardrobeItem,
        size_label: str | None = None,
        color: str | None = None,
        fit_notes: str | None = None,
    ) -> WardrobeItem:
        if size_label is not None:
            item.size_label = size_label
        if color is not None:
            item.color = color
        if fit_notes is not None:
            item.fit_notes = fit_notes
        self.session.flush()
        return item

    def delete_item(self, item: WardrobeItem) -> None:
        self.session.delete(item)

    def list_outfits_for_user(self, user_id: int) -> list[WardrobeOutfit]:
        statement = (
            select(WardrobeOutfit)
            .where(WardrobeOutfit.user_id == user_id)
            .order_by(WardrobeOutfit.id)
        )
        return list(self.session.scalars(statement))

    def get_outfit_by_id(self, outfit_id: int, user_id: int) -> WardrobeOutfit | None:
        statement = (
            select(WardrobeOutfit)
            .where(WardrobeOutfit.id == outfit_id, WardrobeOutfit.user_id == user_id)
            .limit(1)
        )
        return self.session.scalar(statement)

    def create_outfit(self, user_id: int, name: str, wardrobe_item_ids: list[int]) -> WardrobeOutfit:
        outfit = WardrobeOutfit(
            user_id=user_id,
            name=name,
            wardrobe_item_ids=json.dumps(wardrobe_item_ids),
        )
        self.session.add(outfit)
        self.session.flush()
        return outfit

    def delete_outfit(self, outfit: WardrobeOutfit) -> None:
        self.session.delete(outfit)
