from __future__ import annotations

from sqlalchemy import Enum, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.ai_try_on_job_status import AITryOnJobStatus
from app.domain.fit_class import FitClass
from app.models.base import Base, TimestampMixin


class AITryOnJob(TimestampMixin, Base):
    __tablename__ = "ai_try_on_jobs"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), index=True, nullable=False)
    source_asset_id: Mapped[int] = mapped_column(ForeignKey("ai_assets.id"), nullable=False)
    result_asset_id: Mapped[int | None] = mapped_column(ForeignKey("ai_assets.id"), nullable=True)
    idempotency_key: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    fit_class: Mapped[FitClass] = mapped_column(
        Enum(FitClass, name="fit_class", native_enum=False),
        index=True,
        nullable=False,
    )
    fit_reason: Mapped[str] = mapped_column(String(100), nullable=False)
    provider_name: Mapped[str] = mapped_column(String(50), nullable=False, default="openrouter", server_default="openrouter")
    primary_model_name: Mapped[str] = mapped_column(String(150), nullable=False)
    fallback_model_name: Mapped[str] = mapped_column(String(150), nullable=False)
    selected_model_name: Mapped[str | None] = mapped_column(String(150), nullable=True)
    prompt_template_version: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[AITryOnJobStatus] = mapped_column(
        Enum(AITryOnJobStatus, name="ai_try_on_job_status", native_enum=False),
        index=True,
        nullable=False,
        default=AITryOnJobStatus.QUEUED,
        server_default=AITryOnJobStatus.QUEUED.value,
    )
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    max_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=2, server_default="2")
    request_snapshot: Mapped[dict] = mapped_column(JSON, nullable=False)
    deterministic_snapshot: Mapped[dict] = mapped_column(JSON, nullable=False)
    last_ai_call_id: Mapped[int | None] = mapped_column(ForeignKey("ai_call_records.id"), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
