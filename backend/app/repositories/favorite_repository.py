from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.models.favorite import Favorite
from app.models.product import Product


class FavoriteRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_for_user(self, user_id: int) -> list[Favorite]:
        statement = (
            select(Favorite)
            .options(joinedload(Favorite.product).selectinload(Product.translations))
            .where(Favorite.user_id == user_id)
            .order_by(Favorite.id)
        )
        return list(self.session.scalars(statement).unique())

    def get_by_user_and_product(self, user_id: int, product_id: int) -> Favorite | None:
        statement = select(Favorite).where(Favorite.user_id == user_id, Favorite.product_id == product_id).limit(1)
        return self.session.scalar(statement)

    def create(self, user_id: int, product_id: int) -> Favorite:
        favorite = Favorite(user_id=user_id, product_id=product_id)
        self.session.add(favorite)
        self.session.flush()
        return favorite

    def delete(self, user_id: int, product_id: int) -> None:
        self.session.execute(delete(Favorite).where(Favorite.user_id == user_id, Favorite.product_id == product_id))
