from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.size_chart import SizeChartRecord
from app.schemas.sizing import SizeChart


class SizeChartRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_id(self, chart_id: int) -> SizeChart | None:
        record = self.session.get(SizeChartRecord, chart_id)
        if record is None:
            return None
        return SizeChart.model_validate(record)
