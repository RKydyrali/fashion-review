from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.common import Money, PriceBreakdown
from app.schemas.product import ProductRead


class BagItemCreate(BaseModel):
    product_id: int
    size_label: str
    quantity: int = Field(default=1, gt=0)


class BagItemPatch(BaseModel):
    size_label: str | None = None
    quantity: int | None = Field(default=None, gt=0)


class BagItemRead(BaseModel):
    id: int
    product: ProductRead
    size_label: str
    quantity: int
    price_breakdown: PriceBreakdown
    line_total: Money


class BagSummaryRead(BaseModel):
    items: list[BagItemRead]
    subtotal: Money
    total_adjustments: Money
    grand_total: Money
