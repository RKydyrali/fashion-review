from __future__ import annotations

from sqlalchemy import JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class SizeChartRecord(Base):
    __tablename__ = "size_charts"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    sizes: Mapped[list[dict[str, float | str]]] = mapped_column(JSON, default=list, nullable=False)
