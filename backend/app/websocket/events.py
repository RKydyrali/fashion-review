from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field

from app.domain.order_deadline_stage import OrderDeadlineStage
from app.domain.order_status import OrderStatus


class SubscriptionCommand(BaseModel):
    command: Literal["subscribe", "unsubscribe"]
    channel: str


class ChannelCommandPayload(BaseModel):
    channel: str


class ErrorPayload(BaseModel):
    message: str
    channel: str | None = None


class OrderRealtimePayload(BaseModel):
    order_id: int
    client_id: int
    branch_id: int
    previous_branch_id: int | None = None
    product_id: int
    quantity: int
    branch_attempt_count: int
    current_deadline_at: datetime | None = None
    current_deadline_stage: OrderDeadlineStage | None = None
    cancellation_reason: str | None = None
    escalation_reason: str | None = None
    status: OrderStatus
    previous_status: OrderStatus | None = None
    note: str | None = None


class RealtimeEvent(BaseModel):
    event: str
    channels: list[str] = Field(default_factory=list)
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    payload: dict[str, Any]
