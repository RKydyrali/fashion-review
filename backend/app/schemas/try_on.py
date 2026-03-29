from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from app.domain.try_on_status import TryOnStatus


class TryOnSessionRead(BaseModel):
    id: int
    status: TryOnStatus
    source_image_url: str
    rendered_image_url: str | None
    product_ids: list[int]
    attempt_count: int
    error_message: str | None
    created_at: datetime
    updated_at: datetime


class TryOnRealtimePayload(BaseModel):
    session_id: int
    user_id: int
    status: TryOnStatus
    rendered_image_url: str | None = None
    error_message: str | None = None
