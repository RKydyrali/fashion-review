from __future__ import annotations

from dataclasses import dataclass

AVISHU_SIZE_LABELS = [
    "XS",
    "S",
    "M",
    "L",
    "XL",
    "2XL",
    "3XL",
    "4XL",
    "5XL",
    "6XL",
]
EXTENDED_TAILORING_SIZES = {"4XL", "5XL", "6XL"}
EXTENDED_TAILORING_MULTIPLIER = 0.20
EXTENDED_TAILORING_LABEL = "Extended size tailoring"
DEFAULT_CURRENCY = "USD"


@dataclass(frozen=True)
class PriceBreakdownData:
    base_price_minor: int
    tailoring_adjustment_minor: int
    total_price_minor: int
    currency: str
    adjustment_label: str | None


def compute_price_breakdown(base_price_minor: int, size_label: str, currency: str = DEFAULT_CURRENCY) -> PriceBreakdownData:
    normalized_size = size_label.strip().upper()
    adjustment_minor = 0
    adjustment_label: str | None = None
    if normalized_size in EXTENDED_TAILORING_SIZES:
        adjustment_minor = int(round(base_price_minor * EXTENDED_TAILORING_MULTIPLIER))
        adjustment_label = EXTENDED_TAILORING_LABEL
    total_price_minor = base_price_minor + adjustment_minor
    return PriceBreakdownData(
        base_price_minor=base_price_minor,
        tailoring_adjustment_minor=adjustment_minor,
        total_price_minor=total_price_minor,
        currency=currency,
        adjustment_label=adjustment_label,
    )
