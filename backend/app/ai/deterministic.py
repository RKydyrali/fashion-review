from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256

from app.domain.fit_class import FitClass
from app.domain.product_taxonomy import NormalizedCategory
from app.schemas.sizing import BodyMeasurements, SizeRecommendationRequest
from app.services.size_recommendation_service import SizeRecommendationService


@dataclass(frozen=True)
class FitComputationResult:
    fit_class: FitClass
    fit_reason: str
    deterministic_snapshot: dict


def build_ai_try_on_idempotency_key(
    image_bytes: bytes,
    product_ids: list[int],
    fit_class: str,
    *,
    primary_model_name: str,
    prompt_template_version: str,
) -> str:
    payload = (
        image_bytes
        + b"|"
        + ",".join(str(product_id) for product_id in product_ids).encode("utf-8")
        + b"|"
        + fit_class.encode("utf-8")
        + b"|"
        + primary_model_name.encode("utf-8")
        + b"|"
        + prompt_template_version.encode("utf-8")
    )
    return sha256(payload).hexdigest()


def compute_fit_class(
    *,
    normalized_category: str,
    body_measurements: BodyMeasurements | None,
    product_measurements: dict | None,
    preferred_fit: str | None,
    chart_id: int | None,
    size_service: SizeRecommendationService,
) -> FitComputationResult:
    if body_measurements is not None and product_measurements:
        ease_values = []
        for field_name in ("chest", "waist", "hips"):
            body_value = getattr(body_measurements, f"{field_name}_cm", None)
            product_value = product_measurements.get(f"{field_name}_cm")
            if body_value is None or product_value is None:
                continue
            ease_values.append((product_value - body_value) / max(body_value, 1.0))
        if ease_values:
            average_ease = sum(ease_values) / len(ease_values)
            if average_ease <= 0.02:
                return FitComputationResult(
                    fit_class=FitClass.CLOSE,
                    fit_reason="product_measurements_close_fit",
                    deterministic_snapshot={"average_ease": round(average_ease, 4)},
                )
            if average_ease <= 0.06:
                return FitComputationResult(
                    fit_class=FitClass.REGULAR,
                    fit_reason="product_measurements_regular_fit",
                    deterministic_snapshot={"average_ease": round(average_ease, 4)},
                )
            if average_ease <= 0.12:
                return FitComputationResult(
                    fit_class=FitClass.RELAXED,
                    fit_reason="product_measurements_relaxed_fit",
                    deterministic_snapshot={"average_ease": round(average_ease, 4)},
                )
            return FitComputationResult(
                fit_class=FitClass.OVERSIZED,
                fit_reason="product_measurements_oversized_fit",
                deterministic_snapshot={"average_ease": round(average_ease, 4)},
            )

    if preferred_fit == "slim":
        return FitComputationResult(
            fit_class=FitClass.CLOSE,
            fit_reason="preferred_fit_slim",
            deterministic_snapshot={"preferred_fit": preferred_fit},
        )
    if preferred_fit == "oversized":
        return FitComputationResult(
            fit_class=FitClass.OVERSIZED,
            fit_reason="preferred_fit_oversized",
            deterministic_snapshot={"preferred_fit": preferred_fit},
        )

    if body_measurements is not None:
        recommendation = size_service.recommend_size(
            SizeRecommendationRequest(
                chart_id=chart_id or 1,
                fit_type="regular",
                measurements=body_measurements,
            )
        )
        if normalized_category == NormalizedCategory.OUTERWEAR.value:
            return FitComputationResult(
                fit_class=FitClass.RELAXED,
                fit_reason="outerwear_category_default",
                deterministic_snapshot=recommendation.model_dump(mode="json"),
            )
        return FitComputationResult(
            fit_class=FitClass.REGULAR,
            fit_reason="size_service_regular_fit",
            deterministic_snapshot=recommendation.model_dump(mode="json"),
        )

    if normalized_category == NormalizedCategory.OUTERWEAR.value:
        return FitComputationResult(
            fit_class=FitClass.RELAXED,
            fit_reason="category_heuristic_outerwear",
            deterministic_snapshot={"normalized_category": normalized_category},
        )

    return FitComputationResult(
        fit_class=FitClass.REGULAR,
        fit_reason="category_heuristic_regular",
        deterministic_snapshot={"normalized_category": normalized_category},
    )
