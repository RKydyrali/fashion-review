from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.domain.order_deadline_stage import OrderDeadlineStage
from app.domain.order_event_type import OrderEventType
from app.domain.order_status import OrderStatus
from app.domain.roles import UserRole
from app.schemas.common import Money, PriceBreakdown


class UserContext(BaseModel):
    id: int
    role: UserRole
    branch_id: int | None = None


class OrderCreate(BaseModel):
    product_id: int
    branch_id: int | None = None
    quantity: int = Field(gt=0)
    delivery_city: str | None = None
    size_label: str | None = None
    preorder_batch_id: int | None = None


class OrderStatusUpdate(BaseModel):
    status: OrderStatus
    note: str | None = None


class OrderRejectRequest(BaseModel):
    note: str


class OrderCancelRequest(BaseModel):
    reason: str


class OrderEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: int
    order_id: int
    actor_user_id: int | None
    event_type: OrderEventType
    from_status: OrderStatus | None
    to_status: OrderStatus
    note: str | None
    metadata: dict[str, Any] | None = Field(default=None, alias="event_metadata")


class OrderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    client_id: int
    product_id: int
    branch_id: int
    preorder_batch_id: int | None
    delivery_city: str | None
    size_label: str | None
    quantity: int
    unit_price: Money | None = None
    price_breakdown: PriceBreakdown | None = None
    line_total: Money | None = None
    branch_attempt_count: int
    current_deadline_at: datetime | None
    current_deadline_stage: OrderDeadlineStage | None
    cancellation_reason: str | None
    escalation_reason: str | None
    status: OrderStatus
    events: list[OrderEventRead] = Field(default_factory=list)
    product: dict[str, Any] | None = None
