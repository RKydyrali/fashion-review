from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.ai_call_record import AICallRecord


class AICallRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, **values) -> AICallRecord:
        record = AICallRecord(**values)
        self.session.add(record)
        self.session.flush()
        return record
