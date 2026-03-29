from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.collection import Collection


class CollectionRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_all(self) -> list[Collection]:
        statement = select(Collection).where(Collection.is_active.is_(True)).order_by(Collection.sort_order, Collection.id)
        return list(self.session.scalars(statement))

    def get_by_slug(self, slug: str) -> Collection | None:
        statement = select(Collection).where(Collection.slug == slug, Collection.is_active.is_(True)).limit(1)
        return self.session.scalar(statement)
