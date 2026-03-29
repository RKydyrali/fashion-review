from sqlalchemy.orm import Session

from app.domain.language import DEFAULT_LANGUAGE, LanguageCode
from app.models.collection import Collection
from app.repositories.collection_repository import CollectionRepository
from app.repositories.product_repository import ProductRepository
from app.schemas.collection import CollectionRead, EditorialFeedSectionRead, FeedHeroRead, FeedRead
from app.schemas.product import ProductDetailRead, ProductRead
from app.services.product_localization import to_product_detail_read, to_product_read


class CatalogService:
    def __init__(
        self,
        session: Session,
        repository: ProductRepository | None = None,
    ) -> None:
        self.repository = repository or ProductRepository(session)
        self.collection_repository = CollectionRepository(session)
        self.default_language = DEFAULT_LANGUAGE

    def list_products(self, language: LanguageCode) -> list[ProductRead]:
        return [
            to_product_read(product, language, fallback_language=self.default_language)
            for product in self.repository.list_all()
        ]

    def get_product_by_slug(self, slug: str, language: LanguageCode) -> ProductDetailRead | None:
        product = self.repository.get_by_slug(slug)
        if product is None:
            return None
        return to_product_detail_read(product, language, fallback_language=self.default_language)

    def list_collections(self, language: LanguageCode) -> list[CollectionRead]:
        collections = self.collection_repository.list_all()
        return [self._to_collection_read(collection, language) for collection in collections]

    def get_feed(self, language: LanguageCode) -> FeedRead:
        collections = self.list_collections(language)
        featured_products = [
            to_product_read(product, language, fallback_language=self.default_language)
            for product in self.repository.list_featured()
        ]
        hero_collection = collections[0]
        return FeedRead(
            hero=FeedHeroRead(
                title=hero_collection.title,
                subtitle=hero_collection.summary,
                image_url=hero_collection.hero_image_url,
                collection_slug=hero_collection.slug,
            ),
            collections=collections,
            sections=[
                EditorialFeedSectionRead(
                    slug="featured",
                    title="Featured Edit" if language == LanguageCode.EN else ("Избранный блок" if language == LanguageCode.RU else "Таңдаулы топтама"),
                    eyebrow="AVISHU",
                    products=featured_products,
                ),
                EditorialFeedSectionRead(
                    slug="new-arrivals",
                    title="New Arrivals" if language == LanguageCode.EN else ("Новые поступления" if language == LanguageCode.RU else "Жаңа келім"),
                    eyebrow="Latest",
                    products=[
                        to_product_read(product, language, fallback_language=self.default_language)
                        for product in self.repository.list_all()[:4]
                    ],
                ),
            ],
        )

    def _to_collection_read(self, collection: Collection, language: LanguageCode) -> CollectionRead:
        title = collection.name_translations.get(language.value) or collection.name_translations.get(self.default_language.value) or collection.slug
        summary = collection.summary_translations.get(language.value) or collection.summary_translations.get(self.default_language.value) or ""
        eyebrow = collection.eyebrow_translations.get(language.value) or collection.eyebrow_translations.get(self.default_language.value) or "AVISHU"
        products = [
            to_product_read(product, language, fallback_language=self.default_language)
            for product in self.repository.list_by_collection_slug(collection.slug)
        ]
        return CollectionRead(
            id=collection.id,
            slug=collection.slug,
            eyebrow=eyebrow,
            title=title,
            summary=summary,
            hero_image_url=collection.hero_image_url,
            cover_image_url=collection.cover_image_url,
            is_featured=collection.is_featured,
            products=products,
        )
