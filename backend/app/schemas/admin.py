from __future__ import annotations

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.domain.language import LanguageCode
from app.domain.roles import UserRole
from app.schemas.ai import AIProductTranslationResponse


class AdminBranchSummary(BaseModel):
    id: int
    name: str
    code: str
    city: str
    manager_user_id: int | None


class AdminUserCreate(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=4, max_length=255)
    role: UserRole
    preferred_language: LanguageCode = LanguageCode.EN
    branch_id: int | None = None


class AdminUserUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=255)
    password: str | None = Field(default=None, min_length=4, max_length=255)
    role: UserRole | None = None
    preferred_language: LanguageCode | None = None
    is_active: bool | None = None
    branch_id: int | None = None


class AdminUserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    full_name: str
    role: UserRole
    preferred_language: LanguageCode
    is_active: bool
    branch_id: int | None = None


class AdminProductTranslationInput(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    subtitle: str | None = Field(default=None, max_length=255)
    long_description: str | None = None
    fabric_notes: str | None = None
    care_notes: str | None = None
    preorder_note: str | None = None
    display_category: str = Field(min_length=1, max_length=100)


class AdminProductTranslationsInput(BaseModel):
    en: AdminProductTranslationInput
    ru: AdminProductTranslationInput
    kk: AdminProductTranslationInput


class AdminProductTranslationsPatch(BaseModel):
    en: AdminProductTranslationInput | None = None
    ru: AdminProductTranslationInput | None = None
    kk: AdminProductTranslationInput | None = None


class AdminProductTranslationGenerateRequest(BaseModel):
    english: AdminProductTranslationInput
    normalized_category: str | None = Field(default=None, max_length=20)
    color: str | None = Field(default=None, max_length=50)
    season_tags: list[str] = Field(default_factory=list)


class AdminCollectionTranslationInput(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    summary: str = Field(min_length=1)
    eyebrow: str = Field(min_length=1, max_length=255)


class AdminCollectionTranslationsInput(BaseModel):
    en: AdminCollectionTranslationInput
    ru: AdminCollectionTranslationInput
    kk: AdminCollectionTranslationInput


class AdminCollectionTranslationsPatch(BaseModel):
    en: AdminCollectionTranslationInput | None = None
    ru: AdminCollectionTranslationInput | None = None
    kk: AdminCollectionTranslationInput | None = None


class AdminProductCreate(BaseModel):
    sku: str = Field(min_length=1, max_length=100)
    slug: str = Field(min_length=1, max_length=160)
    normalized_category: str = Field(min_length=1, max_length=20)
    season_tags: list[str] = Field(default_factory=list)
    color: str = Field(min_length=1, max_length=50)
    base_price_minor: int = Field(ge=0)
    currency: str = Field(min_length=3, max_length=3)
    collection_slug: str | None = Field(default=None, max_length=120)
    hero_image_url: str | None = None
    reference_image_url: str | None = None
    gallery_image_urls: list[str] = Field(default_factory=list)
    available_sizes: list[str] = Field(default_factory=list)
    size_chart_id: int | None = None
    editorial_rank: int = Field(default=1, ge=1)
    is_featured: bool = False
    is_available: bool = True
    is_active: bool = True
    translations: AdminProductTranslationsInput


class AdminProductUpdate(BaseModel):
    sku: str | None = Field(default=None, min_length=1, max_length=100)
    slug: str | None = Field(default=None, min_length=1, max_length=160)
    normalized_category: str | None = Field(default=None, min_length=1, max_length=20)
    season_tags: list[str] | None = None
    color: str | None = Field(default=None, min_length=1, max_length=50)
    base_price_minor: int | None = Field(default=None, ge=0)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    collection_slug: str | None = Field(default=None, max_length=120)
    hero_image_url: str | None = None
    reference_image_url: str | None = None
    gallery_image_urls: list[str] | None = None
    available_sizes: list[str] | None = None
    size_chart_id: int | None = None
    editorial_rank: int | None = Field(default=None, ge=1)
    is_featured: bool | None = None
    is_available: bool | None = None
    is_active: bool | None = None
    translations: AdminProductTranslationsPatch | None = None


class AdminProductRead(BaseModel):
    id: int
    sku: str
    slug: str
    normalized_category: str
    season_tags: list[str]
    color: str
    base_price_minor: int
    currency: str
    collection_slug: str | None
    hero_image_url: str | None
    reference_image_url: str | None
    gallery_image_urls: list[str]
    available_sizes: list[str]
    size_chart_id: int | None
    editorial_rank: int
    is_featured: bool
    is_available: bool
    is_active: bool
    translations: AdminProductTranslationsInput


class AdminCollectionCreate(BaseModel):
    slug: str = Field(min_length=1, max_length=120)
    hero_image_url: str
    cover_image_url: str
    sort_order: int = Field(default=1, ge=1)
    is_featured: bool = True
    is_active: bool = True
    translations: AdminCollectionTranslationsInput


class AdminCollectionUpdate(BaseModel):
    slug: str | None = Field(default=None, min_length=1, max_length=120)
    hero_image_url: str | None = None
    cover_image_url: str | None = None
    sort_order: int | None = Field(default=None, ge=1)
    is_featured: bool | None = None
    is_active: bool | None = None
    translations: AdminCollectionTranslationsPatch | None = None


class AdminCollectionRead(BaseModel):
    id: int
    slug: str
    hero_image_url: str
    cover_image_url: str
    sort_order: int
    is_featured: bool
    is_active: bool
    translations: AdminCollectionTranslationsInput


class AdminMediaUploadRead(BaseModel):
    url: str
    relative_path: str


class AdminProductTranslationGenerateResponse(AIProductTranslationResponse):
    pass
