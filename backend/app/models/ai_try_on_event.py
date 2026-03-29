from __future__ import annotations

from sqlalchemy import ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, CreatedAtMixin


class AITryOnEvent(CreatedAtMixin, Base):
    __tablename__ = "ai_try_on_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("ai_try_on_jobs.id", ondelete="CASCADE"), index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)
