from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.domain.language import LanguageCode
from app.repositories.favorite_repository import FavoriteRepository
from app.repositories.product_repository import ProductRepository
from app.schemas.favorite import FavoriteRead
from app.services.product_localization import to_product_read


class FavoriteService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.favorites = FavoriteRepository(session)
        self.products = ProductRepository(session)

    def list_for_user(self, user_id: int, language: LanguageCode) -> list[FavoriteRead]:
        return [
            FavoriteRead(id=favorite.id, product=to_product_read(favorite.product, language))
            for favorite in self.favorites.list_for_user(user_id)
        ]

    def create(self, user_id: int, product_id: int, language: LanguageCode) -> FavoriteRead:
        product = self.products.list_by_ids([product_id])
        if not product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
        favorite = self.favorites.get_by_user_and_product(user_id, product_id)
        if favorite is None:
            favorite = self.favorites.create(user_id, product_id)
            self.session.commit()
            self.session.refresh(favorite)
        return FavoriteRead(id=favorite.id, product=to_product_read(product[0], language))

    def delete(self, user_id: int, product_id: int) -> None:
        self.favorites.delete(user_id, product_id)
        self.session.commit()
