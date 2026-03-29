from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from app.domain.product_taxonomy import normalize_color, normalize_display_category

CanonicalCategory = Literal["top", "bottom", "outerwear"]


class WardrobeCatalogItemInput(BaseModel):
    id: int
    sku: str
    name: str
    display_category: str
    season_tags: list[str] = Field(min_length=1)
    color: str
    is_available: bool = True
    is_active: bool = True
    normalized_category: CanonicalCategory | None = None

    @field_validator("display_category")
    @classmethod
    def validate_display_category(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("display_category must not be empty")
        return cleaned

    @field_validator("season_tags")
    @classmethod
    def validate_season_tags(cls, value: list[str]) -> list[str]:
        cleaned = [tag.strip() for tag in value if tag.strip()]
        if not cleaned:
            raise ValueError("season_tags must include at least one value")
        return cleaned

    @field_validator("color")
    @classmethod
    def validate_color(cls, value: str) -> str:
        cleaned = normalize_color(value)
        if not cleaned:
            raise ValueError("color must not be empty")
        return cleaned

    @model_validator(mode="after")
    def derive_normalized_category(self) -> "WardrobeCatalogItemInput":
        normalized = self.normalized_category or normalize_display_category(self.display_category)
        if normalized is None:
            raise ValueError("display_category is not supported for capsule wardrobe generation")
        self.normalized_category = normalized.value if hasattr(normalized, "value") else normalized
        return self


class WardrobeItemRead(BaseModel):
    id: int
    sku: str
    name: str
    display_category: str
    normalized_category: CanonicalCategory
    season_tags: list[str]
    color: str
    is_available: bool
    is_active: bool


class CapsuleOutfitRead(BaseModel):
    items: list[WardrobeItemRead]
    colors: list[str]
    explanation: str


class CapsuleWardrobeRequest(BaseModel):
    season: str
    allowed_categories: list[CanonicalCategory] = Field(
        default_factory=lambda: ["top", "bottom", "outerwear"]
    )
    max_outfits: int = Field(default=4, ge=1, le=8)
    target_item_limit: int = Field(default=6, ge=3, le=12)
    catalog: list[WardrobeCatalogItemInput] | None = None

    @field_validator("season")
    @classmethod
    def validate_season(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("season must not be empty")
        return cleaned

    @field_validator("allowed_categories")
    @classmethod
    def validate_allowed_categories(
        cls,
        value: list[CanonicalCategory],
    ) -> list[CanonicalCategory]:
        if not value:
            raise ValueError("allowed_categories must not be empty")
        if len(set(value)) != len(value):
            raise ValueError("allowed_categories must be unique")
        return value


class CapsuleWardrobeResponse(BaseModel):
    capsule_items: list[WardrobeItemRead]
    outfits: list[CapsuleOutfitRead]
    summary: str


class WardrobeItemCreate(BaseModel):
    product_id: int
    size_label: str
    color: str | None = None
    fit_notes: str | None = None


class WardrobeItemUpdate(BaseModel):
    size_label: str | None = None
    color: str | None = None
    fit_notes: str | None = None


class WardrobeItemRead(BaseModel):
    id: int
    product_id: int
    size_label: str
    color: str | None
    fit_notes: str | None
    is_from_order: bool
    order_id: int | None
    product_name: str
    product_image: str | None
    product_category: str
    product_color: str
    product_price_minor: int

    class Config:
        from_attributes = True


class WardrobeOutfitCreate(BaseModel):
    name: str
    wardrobe_item_ids: list[int]


class WardrobeOutfitRead(BaseModel):
    id: int
    name: str
    wardrobe_item_ids: list[int]
    items: list[WardrobeItemRead]

    class Config:
        from_attributes = True


class WardrobeSummary(BaseModel):
    items: list[WardrobeItemRead]
    outfits: list[WardrobeOutfitRead]
    total_items: int
    total_outfits: int
