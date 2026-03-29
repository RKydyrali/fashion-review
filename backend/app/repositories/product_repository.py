from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.product import Product


class ProductRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_all(self) -> list[Product]:
        statement = (
            select(Product)
            .options(selectinload(Product.translations))
            .where(Product.is_active.is_(True))
            .order_by(Product.editorial_rank, Product.id)
        )
        return list(self.session.scalars(statement).all())

    def list_by_ids(self, product_ids: list[int]) -> list[Product]:
        statement = (
            select(Product)
            .options(selectinload(Product.translations))
            .where(Product.id.in_(product_ids))
        )
        products = self.session.scalars(statement).all()
        by_id = {product.id: product for product in products}
        return [by_id[product_id] for product_id in product_ids if product_id in by_id]

    def get_by_slug(self, slug: str) -> Product | None:
        statement = (
            select(Product)
            .options(selectinload(Product.translations))
            .where(Product.slug == slug, Product.is_active.is_(True))
            .limit(1)
        )
        return self.session.scalar(statement)

    def list_featured(self) -> list[Product]:
        statement = (
            select(Product)
            .options(selectinload(Product.translations))
            .where(Product.is_featured.is_(True), Product.is_active.is_(True))
            .order_by(Product.editorial_rank, Product.id)
        )
        return list(self.session.scalars(statement).all())

    def list_by_collection_slug(self, collection_slug: str) -> list[Product]:
        statement = (
            select(Product)
            .options(selectinload(Product.translations))
            .where(Product.collection_slug == collection_slug, Product.is_active.is_(True))
            .order_by(Product.editorial_rank, Product.id)
        )
        return list(self.session.scalars(statement).all())
