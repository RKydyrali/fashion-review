from __future__ import annotations

from enum import StrEnum


class NormalizedCategory(StrEnum):
    TOP = "top"
    BOTTOM = "bottom"
    OUTERWEAR = "outerwear"


NEUTRAL_COLORS = {"black", "white", "beige", "gray"}

_CATEGORY_NORMALIZATION_MAP = {
    "outerwear": NormalizedCategory.OUTERWEAR,
    "верхняя одежда": NormalizedCategory.OUTERWEAR,
    "сырт киім": NormalizedCategory.OUTERWEAR,
    "ріўсерхнҫџҫџ рѕрґрµр¶рґр°": NormalizedCategory.OUTERWEAR,
    "basics": NormalizedCategory.TOP,
    "basic": NormalizedCategory.TOP,
    "база": NormalizedCategory.TOP,
    "негізгі киім": NormalizedCategory.TOP,
    "р±р°р·р°": NormalizedCategory.TOP,
    "cardigans": NormalizedCategory.TOP,
    "кардиганы и кофты": NormalizedCategory.TOP,
    "кардигандар мен жемпірлер": NormalizedCategory.TOP,
    "рљр°сђрґрёрір°рнс‹ рё рєрѕс„с‚с‹": NormalizedCategory.TOP,
    "suits": NormalizedCategory.TOP,
    "костюмы": NormalizedCategory.TOP,
    "костюмдер": NormalizedCategory.TOP,
    "рєрѕсѓс‚сћрјс‹": NormalizedCategory.TOP,
    "blouses": NormalizedCategory.TOP,
    "блузы": NormalizedCategory.TOP,
    "жейделер": NormalizedCategory.TOP,
    "р±р»сѓр·с‹": NormalizedCategory.TOP,
    "shirts": NormalizedCategory.TOP,
    "рубашки": NormalizedCategory.TOP,
    "көйлектер": NormalizedCategory.TOP,
    "сђсѓр±р°с€рєрё": NormalizedCategory.TOP,
    "t-shirts": NormalizedCategory.TOP,
    "футболки": NormalizedCategory.TOP,
    "футболкалар": NormalizedCategory.TOP,
    "с„сѓс‚р±рѕр»рєрё": NormalizedCategory.TOP,
    "tops": NormalizedCategory.TOP,
    "топы": NormalizedCategory.TOP,
    "топтар": NormalizedCategory.TOP,
    "с‚рѕрїс‹": NormalizedCategory.TOP,
    "trousers": NormalizedCategory.BOTTOM,
    "брюки": NormalizedCategory.BOTTOM,
    "шалбар": NormalizedCategory.BOTTOM,
    "р±сђсћрєрё": NormalizedCategory.BOTTOM,
    "skirts": NormalizedCategory.BOTTOM,
    "юбки": NormalizedCategory.BOTTOM,
    "юбкалар": NormalizedCategory.BOTTOM,
    "сћр±рєрё": NormalizedCategory.BOTTOM,
    "jeans": NormalizedCategory.BOTTOM,
    "джинсы": NormalizedCategory.BOTTOM,
    "джинсылар": NormalizedCategory.BOTTOM,
    "рґр¶рёрнсѓс‹": NormalizedCategory.BOTTOM,
    "shorts": NormalizedCategory.BOTTOM,
    "шорты": NormalizedCategory.BOTTOM,
    "шортылар": NormalizedCategory.BOTTOM,
    "с€рѕсђс‚с‹": NormalizedCategory.BOTTOM,
}


def normalize_display_category(display_category: str) -> NormalizedCategory | None:
    normalized_key = display_category.strip().casefold()
    return _CATEGORY_NORMALIZATION_MAP.get(normalized_key)


def normalize_color(color: str) -> str:
    return color.strip().casefold()
