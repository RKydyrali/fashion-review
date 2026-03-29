from __future__ import annotations

from pydantic import BaseModel

from app.schemas.product import ProductRead


class CollectionRead(BaseModel):
    id: int
    slug: str
    eyebrow: str
    title: str
    summary: str
    hero_image_url: str
    cover_image_url: str
    is_featured: bool
    products: list[ProductRead]


class FeedHeroRead(BaseModel):
    title: str
    subtitle: str
    image_url: str
    collection_slug: str | None = None


class EditorialFeedSectionRead(BaseModel):
    slug: str
    title: str
    eyebrow: str
    products: list[ProductRead]


class FeedRead(BaseModel):
    hero: FeedHeroRead
    collections: list[CollectionRead]
    sections: list[EditorialFeedSectionRead]
