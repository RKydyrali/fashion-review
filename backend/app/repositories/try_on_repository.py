from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.try_on_status import TryOnStatus
from app.models.try_on_session import TryOnSession


class TryOnRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_id(self, session_id: int) -> TryOnSession | None:
        return self.session.get(TryOnSession, session_id)

    def find_reusable_by_idempotency(self, *, user_id: int, idempotency_key: str) -> TryOnSession | None:
        statement = (
            select(TryOnSession)
            .where(
                TryOnSession.user_id == user_id,
                TryOnSession.idempotency_key == idempotency_key,
                TryOnSession.status.in_(
                    (TryOnStatus.QUEUED, TryOnStatus.PROCESSING, TryOnStatus.COMPLETED)
                ),
            )
            .order_by(TryOnSession.id.desc())
            .limit(1)
        )
        return self.session.scalar(statement)

    def next_queued(self) -> TryOnSession | None:
        statement = (
            select(TryOnSession)
            .where(TryOnSession.status == TryOnStatus.QUEUED)
            .order_by(TryOnSession.id)
            .limit(1)
        )
        return self.session.scalar(statement)

    def save(self, session_model: TryOnSession) -> TryOnSession:
        self.session.add(session_model)
        self.session.flush()
        return session_model
