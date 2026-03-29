from __future__ import annotations

import json
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.domain.language import LanguageCode
from app.models.wardrobe import WardrobeItem, WardrobeOutfit
from app.repositories.product_repository import ProductRepository
from app.repositories.wardrobe_repository import WardrobeRepository
from app.schemas.wardrobe import (
    WardrobeItemCreate,
    WardrobeItemUpdate,
    WardrobeItemRead,
    WardrobeOutfitCreate,
    WardrobeOutfitRead,
    WardrobeSummary,
)


class PersonalWardrobeService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.wardrobe = WardrobeRepository(session)
        self.products = ProductRepository(session)

    def list_items(self, user_id: int) -> list[WardrobeItemRead]:
        items = self.wardrobe.list_items_for_user(user_id)
        return [self._to_item_read(item) for item in items]

    def get_item(self, user_id: int, item_id: int) -> WardrobeItemRead:
        item = self.wardrobe.get_item_by_id(item_id, user_id)
        if item is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wardrobe item not found")
        return self._to_item_read(item)

    def add_item(self, user_id: int, payload: WardrobeItemCreate) -> WardrobeItemRead:
        existing = self.wardrobe.get_by_user_and_product(user_id, payload.product_id)
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Item already in wardrobe",
            )

        products = self.products.list_by_ids([payload.product_id])
        if not products:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

        product = products[0]
        if payload.size_label not in product.available_sizes:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Size is not available for this product",
            )

        item = self.wardrobe.create_item(
            user_id=user_id,
            product_id=payload.product_id,
            size_label=payload.size_label,
            color=payload.color or product.color,
            fit_notes=payload.fit_notes,
        )
        self.session.commit()
        return self._to_item_read(item)

    def update_item(
        self,
        user_id: int,
        item_id: int,
        payload: WardrobeItemUpdate,
    ) -> WardrobeItemRead:
        item = self.wardrobe.get_item_by_id(item_id, user_id)
        if item is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wardrobe item not found")

        if payload.size_label is not None and payload.size_label not in item.product.available_sizes:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Size is not available for this product",
            )

        updated_item = self.wardrobe.update_item(
            item,
            size_label=payload.size_label,
            color=payload.color,
            fit_notes=payload.fit_notes,
        )
        self.session.commit()
        return self._to_item_read(updated_item)

    def remove_item(self, user_id: int, item_id: int) -> None:
        item = self.wardrobe.get_item_by_id(item_id, user_id)
        if item is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wardrobe item not found")
        self.wardrobe.delete_item(item)
        self.session.commit()

    def list_outfits(self, user_id: int) -> list[WardrobeOutfitRead]:
        outfits = self.wardrobe.list_outfits_for_user(user_id)
        return [self._to_outfit_read(outfit) for outfit in outfits]

    def create_outfit(self, user_id: int, payload: WardrobeOutfitCreate) -> WardrobeOutfitRead:
        for item_id in payload.wardrobe_item_ids:
            item = self.wardrobe.get_item_by_id(item_id, user_id)
            if item is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Wardrobe item {item_id} not found",
                )

        outfit = self.wardrobe.create_outfit(
            user_id=user_id,
            name=payload.name,
            wardrobe_item_ids=payload.wardrobe_item_ids,
        )
        self.session.commit()
        return self._to_outfit_read(outfit)

    def delete_outfit(self, user_id: int, outfit_id: int) -> None:
        outfit = self.wardrobe.get_outfit_by_id(outfit_id, user_id)
        if outfit is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Outfit not found")
        self.wardrobe.delete_outfit(outfit)
        self.session.commit()

    def get_summary(self, user_id: int) -> WardrobeSummary:
        items = self.list_items(user_id)
        outfits = self.list_outfits(user_id)
        return WardrobeSummary(
            items=items,
            outfits=outfits,
            total_items=len(items),
            total_outfits=len(outfits),
        )

    def _to_item_read(self, item: WardrobeItem) -> WardrobeItemRead:
        product = item.product
        return WardrobeItemRead(
            id=item.id,
            product_id=item.product_id,
            size_label=item.size_label,
            color=item.color,
            fit_notes=item.fit_notes,
            is_from_order=item.is_from_order,
            order_id=item.order_id,
            product_name=product.name,
            product_image=product.hero_image_url,
            product_category=product.display_category,
            product_color=product.color,
            product_price_minor=product.base_price_minor,
        )

    def _to_outfit_read(self, outfit: WardrobeOutfit) -> WardrobeOutfitRead:
        item_ids = json.loads(outfit.wardrobe_item_ids)
        items = []
        for item_id in item_ids:
            item = self.wardrobe.get_item_by_id(item_id, outfit.user_id)
            if item is not None:
                items.append(self._to_item_read(item))

        return WardrobeOutfitRead(
            id=outfit.id,
            name=outfit.name,
            wardrobe_item_ids=item_ids,
            items=items,
        )
