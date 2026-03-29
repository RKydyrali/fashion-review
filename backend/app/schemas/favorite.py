from __future__ import annotations

from pydantic import BaseModel

from app.schemas.product import ProductRead


class FavoriteCreate(BaseModel):
    product_id: int


class FavoriteRead(BaseModel):
    id: int
    product: ProductRead
