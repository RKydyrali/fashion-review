from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.refresh_session import RefreshSession


class RefreshSessionRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, *, user_id: int, token: str, expires_at: datetime) -> RefreshSession:
        refresh_session = RefreshSession(user_id=user_id, token=token, expires_at=expires_at, revoked_at=None)
        self.session.add(refresh_session)
        self.session.flush()
        return refresh_session

    def get_by_token(self, token: str) -> RefreshSession | None:
        statement = select(RefreshSession).where(RefreshSession.token == token).limit(1)
        return self.session.scalar(statement)

    def revoke(self, refresh_session: RefreshSession, *, revoked_at: datetime) -> RefreshSession:
        refresh_session.revoked_at = revoked_at
        self.session.add(refresh_session)
        self.session.flush()
        return refresh_session
