from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.common import Money
from app.schemas.order import OrderRead


class PreorderSubmitRequest(BaseModel):
    delivery_city: str | None = None


class SelectedPreorderSubmitRequest(PreorderSubmitRequest):
    bag_item_ids: list[int] = Field(min_length=1)


class PreorderBatchRead(BaseModel):
    id: int
    client_id: int
    delivery_city: str | None
    item_count: int
    total_price: Money
    original_price: Money | None = None
    discount_applied: Money | None = None
    discount_percentage: int | None = None
    currency: str
    status: str
    created_at: datetime
    orders: list[OrderRead]
