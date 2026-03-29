from __future__ import annotations

from app.domain.commerce import compute_price_breakdown
from app.domain.language import DEFAULT_LANGUAGE, LanguageCode
from app.models.product import Product
from app.schemas.common import Money, PriceBreakdown
from app.schemas.product import ProductDetailRead, ProductRead, ProductSizeOption
from app.schemas.wardrobe import WardrobeItemRead


def localize_product_fields(
    product: Product,
    language: LanguageCode,
    *,
    fallback_language: LanguageCode = DEFAULT_LANGUAGE,
) -> dict[str, str | None]:
    translations = {translation.language_code: translation for translation in product.translations}
    translation = translations.get(language.value) or translations.get(fallback_language.value)

    return {
        "name": translation.name if translation is not None else product.name,
        "description": translation.description if translation is not None else None,
        "subtitle": (translation.subtitle if translation is not None else product.subtitle),
        "long_description": (translation.long_description if translation is not None else product.long_description),
        "fabric_notes": (translation.fabric_notes if translation is not None else product.fabric_notes),
        "care_notes": (translation.care_notes if translation is not None else product.care_notes),
        "preorder_note": (translation.preorder_note if translation is not None else product.preorder_note),
        "display_category": (
            translation.display_category if translation is not None else product.display_category
        ),
    }


def money(amount_minor: int, currency: str) -> Money:
    return Money(amount_minor=amount_minor, currency=currency, formatted=f"{currency} {amount_minor:,.0f}")


def price_breakdown(amount_minor: int, size_label: str, currency: str) -> PriceBreakdown:
    breakdown = compute_price_breakdown(amount_minor, size_label, currency=currency)
    return PriceBreakdown(
        base_price=money(breakdown.base_price_minor, breakdown.currency),
        tailoring_adjustment=money(breakdown.tailoring_adjustment_minor, breakdown.currency),
        total_price=money(breakdown.total_price_minor, breakdown.currency),
        adjustment_label=breakdown.adjustment_label,
    )


def to_product_read(
    product: Product,
    language: LanguageCode,
    *,
    fallback_language: LanguageCode = DEFAULT_LANGUAGE,
) -> ProductRead:
    localized = localize_product_fields(product, language, fallback_language=fallback_language)
    return ProductRead(
        id=product.id,
        sku=product.sku,
        slug=product.slug,
        name=str(localized["name"]),
        description=localized["description"],
        subtitle=localized["subtitle"],
        display_category=str(localized["display_category"]),
        normalized_category=product.normalized_category,
        season_tags=list(product.season_tags),
        color=product.color,
        base_price=product.base_price_minor,
        currency=product.currency,
        hero_image_url=product.hero_image_url,
        reference_image_url=product.reference_image_url,
        is_available=product.is_available,
        is_active=product.is_active,
        available_sizes=list(product.available_sizes),
    )


def to_product_detail_read(
    product: Product,
    language: LanguageCode,
    *,
    fallback_language: LanguageCode = DEFAULT_LANGUAGE,
) -> ProductDetailRead:
    localized = localize_product_fields(product, language, fallback_language=fallback_language)
    default_size = product.available_sizes[0] if product.available_sizes else "M"
    return ProductDetailRead(
        **to_product_read(product, language, fallback_language=fallback_language).model_dump(),
        long_description=localized["long_description"],
        fabric_notes=localized["fabric_notes"],
        care_notes=localized["care_notes"],
        preorder_note=localized["preorder_note"],
        collection_slug=product.collection_slug,
        gallery_image_urls=list(product.gallery_image_urls),
        size_chart_id=product.size_chart_id,
        price_breakdown=price_breakdown(product.base_price_minor, default_size, product.currency),
        size_options=[
            ProductSizeOption(
                size_label=size_label,
                is_available=product.is_available and product.is_active,
                price_breakdown=price_breakdown(product.base_price_minor, size_label, product.currency),
            )
            for size_label in product.available_sizes
        ],
    )


def to_wardrobe_item_read(
    product: Product,
    language: LanguageCode,
    *,
    fallback_language: LanguageCode = DEFAULT_LANGUAGE,
) -> WardrobeItemRead:
    localized = localize_product_fields(product, language, fallback_language=fallback_language)
    return WardrobeItemRead(
        id=product.id,
        sku=product.sku,
        name=str(localized["name"]),
        display_category=str(localized["display_category"]),
        normalized_category=product.normalized_category,
        season_tags=list(product.season_tags),
        color=product.color,
        is_available=product.is_available,
        is_active=product.is_active,
    )
