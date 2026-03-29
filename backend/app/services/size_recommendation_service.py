from __future__ import annotations

from math import sqrt

from fastapi import HTTPException, status

from app.repositories.size_chart_repository import SizeChartRepository
from app.schemas.sizing import (
    BodyMeasurements,
    SizeChart,
    SizeRange,
    SizeRecommendationRequest,
    SizeRecommendationResponse,
)

MIN_RANGE_WIDTH_CM = 5.0
CONFIDENCE_ORDER = ["low", "medium", "high"]
MEASUREMENT_FIELDS = ("chest", "waist", "hips")


class SizeRecommendationService:
    def __init__(self, repository: SizeChartRepository | None = None) -> None:
        self.repository = repository

    def recommend_size(self, request: SizeRecommendationRequest) -> SizeRecommendationResponse:
        chart = self._resolve_chart(request)
        matched_sizes = self._match_sizes_by_measurement(chart, request.measurements)
        warnings: list[str] = []

        if any(size_label is None for size_label in matched_sizes.values()):
            warnings.append("out_of_chart_bounds")

        if all(size_label is not None for size_label in matched_sizes.values()):
            match_method = "exact_range"
            base_index = max(
                self._size_index(chart, size_label)
                for size_label in matched_sizes.values()
                if size_label is not None
            )
            base_score = 0.0
            if len(set(matched_sizes.values())) > 1:
                warnings.append("split_measurements")
        else:
            match_method = "closest_distance"
            base_index, base_score = self._closest_size_index(chart, request.measurements)
            warnings.append("closest_distance_used")

        base_size = chart.sizes[base_index].size_label
        recommended_index = base_index
        if request.fit_type == "oversized":
            if base_index + 1 < len(chart.sizes):
                recommended_index = base_index + 1
                warnings.append("fit_adjusted_up")
            else:
                warnings.append("fit_adjustment_unavailable")
        elif request.fit_type == "slim":
            if base_index - 1 >= 0:
                recommended_index = base_index - 1
                warnings.append("fit_adjusted_down")
            else:
                warnings.append("fit_adjustment_unavailable")

        confidence = self._confidence_for(
            base_score=base_score,
            match_method=match_method,
            split_measurements="split_measurements" in warnings,
            fit_adjusted=recommended_index != base_index,
        )

        return SizeRecommendationResponse(
            recommended_size=chart.sizes[recommended_index].size_label,
            base_size=base_size,
            confidence=confidence,
            confidence_score=round(base_score, 4),
            match_method=match_method,
            fit_type=request.fit_type,
            warnings=warnings,
            matched_sizes_by_measurement=matched_sizes,
        )

    def _resolve_chart(self, request: SizeRecommendationRequest) -> SizeChart:
        if request.size_chart is not None:
            return request.size_chart
        if self.repository is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Size chart not found")
        chart = self.repository.get_by_id(request.chart_id or 0)
        if chart is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Size chart not found")
        return chart

    def _match_sizes_by_measurement(
        self,
        chart: SizeChart,
        measurements: BodyMeasurements,
    ) -> dict[str, str | None]:
        matched: dict[str, str | None] = {}
        for field_name in MEASUREMENT_FIELDS:
            value = getattr(measurements, f"{field_name}_cm")
            matched[field_name] = next(
                (
                    size.size_label
                    for size in chart.sizes
                    if self._value_in_range(value, getattr(size, f"{field_name}_min_cm"), getattr(size, f"{field_name}_max_cm"))
                ),
                None,
            )
        return matched

    def _closest_size_index(self, chart: SizeChart, measurements: BodyMeasurements) -> tuple[int, float]:
        scored = [
            (index, self._size_distance_score(size, measurements))
            for index, size in enumerate(chart.sizes)
        ]
        scored.sort(key=lambda row: (row[1], -row[0]))
        return scored[0]

    def _size_distance_score(self, size: SizeRange, measurements: BodyMeasurements) -> float:
        squared_distances = []
        for field_name in MEASUREMENT_FIELDS:
            value = getattr(measurements, f"{field_name}_cm")
            minimum = getattr(size, f"{field_name}_min_cm")
            maximum = getattr(size, f"{field_name}_max_cm")
            if self._value_in_range(value, minimum, maximum):
                squared_distances.append(0.0)
                continue
            nearest_boundary_distance = min(abs(value - minimum), abs(value - maximum))
            range_width = max(maximum - minimum, MIN_RANGE_WIDTH_CM)
            squared_distances.append((nearest_boundary_distance / range_width) ** 2)
        return sqrt(sum(squared_distances) / len(squared_distances))

    def _confidence_for(
        self,
        *,
        base_score: float,
        match_method: str,
        split_measurements: bool,
        fit_adjusted: bool,
    ) -> str:
        if match_method == "exact_range" and not split_measurements:
            confidence = "high"
        elif match_method == "exact_range" and split_measurements:
            confidence = "medium"
        elif base_score <= 0.10:
            confidence = "high"
        elif base_score <= 0.30:
            confidence = "medium"
        else:
            confidence = "low"

        if fit_adjusted:
            confidence = self._downgrade_confidence(confidence)
        return confidence

    def _downgrade_confidence(self, confidence: str) -> str:
        current_index = CONFIDENCE_ORDER.index(confidence)
        return CONFIDENCE_ORDER[max(0, current_index - 1)]

    def _size_index(self, chart: SizeChart, size_label: str) -> int:
        for index, size in enumerate(chart.sizes):
            if size.size_label == size_label:
                return index
        raise ValueError(f"Unknown size label: {size_label}")

    def _value_in_range(self, value: float, minimum: float, maximum: float) -> bool:
        return minimum <= value <= maximum
