from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.domain.commerce import compute_price_breakdown
from app.domain.language import LanguageCode
from app.models.bag_item import BagItem
from app.repositories.bag_repository import BagRepository
from app.repositories.product_repository import ProductRepository
from app.schemas.bag import BagItemCreate, BagItemPatch, BagItemRead, BagSummaryRead
from app.services.product_localization import money, price_breakdown, to_product_read


class BagService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.bag = BagRepository(session)
        self.products = ProductRepository(session)

    def list_for_user(self, user_id: int, language: LanguageCode) -> BagSummaryRead:
        items = [self._to_bag_item_read(item, language) for item in self.bag.list_for_user(user_id)]
        subtotal_minor = sum(item.price_breakdown.base_price.amount_minor * item.quantity for item in items)
        adjustments_minor = sum(item.price_breakdown.tailoring_adjustment.amount_minor * item.quantity for item in items)
        grand_total_minor = sum(item.line_total.amount_minor for item in items)
        currency = items[0].line_total.currency if items else "USD"
        return BagSummaryRead(
            items=items,
            subtotal=money(subtotal_minor, currency),
            total_adjustments=money(adjustments_minor, currency),
            grand_total=money(grand_total_minor, currency),
        )

    def add_item(self, user_id: int, payload: BagItemCreate, language: LanguageCode) -> BagItemRead:
        product = self._require_product(payload.product_id)
        self._validate_size(product.available_sizes, payload.size_label)
        existing = self.bag.get_by_unique_key(user_id=user_id, product_id=payload.product_id, size_label=payload.size_label)
        if existing is not None:
            existing.quantity += payload.quantity
            bag_item = self._sync_prices(existing, product)
        else:
            breakdown = compute_price_breakdown(product.base_price_minor, payload.size_label, product.currency)
            bag_item = BagItem(
                user_id=user_id,
                product_id=payload.product_id,
                size_label=payload.size_label,
                quantity=payload.quantity,
                unit_price_minor=breakdown.total_price_minor,
                adjustment_minor=breakdown.tailoring_adjustment_minor,
                line_total_minor=breakdown.total_price_minor * payload.quantity,
                currency=product.currency,
            )
            self.bag.save(bag_item)
        self.session.commit()
        bag_item = self.bag.get_by_id_for_user(bag_item.id, user_id)
        assert bag_item is not None
        return self._to_bag_item_read(bag_item, language)

    def update_item(self, user_id: int, item_id: int, payload: BagItemPatch, language: LanguageCode) -> BagItemRead:
        item = self.bag.get_by_id_for_user(item_id, user_id)
        if item is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bag item not found")
        if payload.size_label is not None:
            self._validate_size(item.product.available_sizes, payload.size_label)
            item.size_label = payload.size_label
        if payload.quantity is not None:
            item.quantity = payload.quantity
        bag_item = self._sync_prices(item, item.product)
        self.session.commit()
        return self._to_bag_item_read(bag_item, language)

    def delete_item(self, user_id: int, item_id: int) -> None:
        item = self.bag.get_by_id_for_user(item_id, user_id)
        if item is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bag item not found")
        self.bag.delete(item)
        self.session.commit()

    def clear_for_user(self, user_id: int) -> None:
        self.bag.clear_for_user(user_id)
        self.session.commit()

    def get_models_for_user(self, user_id: int) -> list[BagItem]:
        return self.bag.list_for_user(user_id)

    def get_models_for_user_by_ids(self, user_id: int, item_ids: list[int]) -> list[BagItem]:
        return self.bag.list_for_user_by_ids(user_id, item_ids)

    def delete_items_for_user(self, user_id: int, item_ids: list[int]) -> None:
        self.bag.delete_for_user_by_ids(user_id, item_ids)

    def _require_product(self, product_id: int):
        products = self.products.list_by_ids([product_id])
        if not products:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
        return products[0]

    def _validate_size(self, available_sizes: list[str], size_label: str) -> None:
        normalized = size_label.strip().upper()
        if normalized not in {size.upper() for size in available_sizes}:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Size is not available")

    def _sync_prices(self, item: BagItem, product) -> BagItem:
        breakdown = compute_price_breakdown(product.base_price_minor, item.size_label, product.currency)
        item.unit_price_minor = breakdown.total_price_minor
        item.adjustment_minor = breakdown.tailoring_adjustment_minor
        item.line_total_minor = breakdown.total_price_minor * item.quantity
        item.currency = product.currency
        return self.bag.save(item)

    def _to_bag_item_read(self, item: BagItem, language: LanguageCode) -> BagItemRead:
        return BagItemRead(
            id=item.id,
            product=to_product_read(item.product, language),
            size_label=item.size_label,
            quantity=item.quantity,
            price_breakdown=price_breakdown(item.product.base_price_minor, item.size_label, item.currency),
            line_total=money(item.line_total_minor, item.currency),
        )
