from __future__ import annotations

from sqlalchemy import Enum, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.try_on_status import TryOnStatus
from app.models.base import Base, TimestampMixin


class TryOnSession(TimestampMixin, Base):
    __tablename__ = "try_on_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    product_ids: Mapped[list[int]] = mapped_column(JSON, default=list, nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    source_image_path: Mapped[str] = mapped_column(String(500), nullable=False)
    rendered_image_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    provider_name: Mapped[str] = mapped_column(String(50), nullable=False, default="flux", server_default="flux")
    status: Mapped[TryOnStatus] = mapped_column(
        Enum(TryOnStatus, name="try_on_status", native_enum=False),
        index=True,
        nullable=False,
        default=TryOnStatus.QUEUED,
        server_default=TryOnStatus.QUEUED.value,
    )
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    max_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=3, server_default="3")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    provider_latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
