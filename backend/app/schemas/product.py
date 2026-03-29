from pydantic import BaseModel, ConfigDict

from app.schemas.common import PriceBreakdown


class ProductRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    sku: str
    slug: str
    name: str
    description: str | None
    subtitle: str | None = None
    display_category: str
    normalized_category: str
    season_tags: list[str]
    color: str
    base_price: int | None = None
    currency: str | None = None
    hero_image_url: str | None = None
    reference_image_url: str | None
    is_available: bool
    is_active: bool
    available_sizes: list[str] = []


class ProductSizeOption(BaseModel):
    size_label: str
    is_available: bool
    price_breakdown: PriceBreakdown


class ProductDetailRead(ProductRead):
    long_description: str | None = None
    fabric_notes: str | None = None
    care_notes: str | None = None
    preorder_note: str | None = None
    collection_slug: str | None = None
    gallery_image_urls: list[str]
    size_chart_id: int | None = None
    price_breakdown: PriceBreakdown
    size_options: list[ProductSizeOption]
