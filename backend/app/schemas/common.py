from pydantic import BaseModel


class MessageResponse(BaseModel):
    message: str


class Money(BaseModel):
    amount_minor: int
    currency: str
    formatted: str


class PriceBreakdown(BaseModel):
    base_price: Money
    tailoring_adjustment: Money
    total_price: Money
    adjustment_label: str | None = None
