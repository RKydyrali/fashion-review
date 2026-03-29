def test_size_recommendation_chooses_larger_exact_size_for_split_measurements() -> None:
    from app.schemas.sizing import BodyMeasurements, SizeChart, SizeRange, SizeRecommendationRequest
    from app.services.size_recommendation_service import SizeRecommendationService

    service = SizeRecommendationService()
    chart = SizeChart(
        name="Split Fit",
        sizes=[
            SizeRange("S", 84, 90, 66, 72, 92, 98),
            SizeRange("M", 91, 97, 73, 79, 99, 105),
            SizeRange("L", 98, 104, 80, 86, 106, 112),
        ],
    )
    result = service.recommend_size(
        SizeRecommendationRequest(
            fit_type="regular",
            measurements=BodyMeasurements(chest_cm=89, waist_cm=75, hips_cm=100),
            size_chart=chart,
        )
    )

    assert result.base_size == "M"
    assert result.recommended_size == "M"
    assert result.match_method == "exact_range"
    assert result.confidence == "medium"
    assert "split_measurements" in result.warnings
    assert result.matched_sizes_by_measurement == {"chest": "S", "waist": "M", "hips": "M"}


def test_size_recommendation_uses_closest_distance_with_minimum_width_clamp_and_out_of_bounds_warning() -> None:
    from app.schemas.sizing import BodyMeasurements, SizeChart, SizeRange, SizeRecommendationRequest
    from app.services.size_recommendation_service import SizeRecommendationService

    service = SizeRecommendationService()
    chart = SizeChart(
        name="Narrow Ranges",
        sizes=[
            SizeRange("A", 89, 90, 69, 70, 94, 95),
            SizeRange("B", 90, 91, 70, 71, 95, 96),
        ],
    )
    result = service.recommend_size(
        SizeRecommendationRequest(
            fit_type="regular",
            measurements=BodyMeasurements(chest_cm=105, waist_cm=83, hips_cm=110),
            size_chart=chart,
        )
    )

    assert result.base_size == "B"
    assert result.recommended_size == "B"
    assert result.match_method == "closest_distance"
    assert result.confidence == "low"
    assert result.confidence_score > 0.30
    assert "closest_distance_used" in result.warnings
    assert "out_of_chart_bounds" in result.warnings


def test_size_recommendation_fit_adjustment_uses_declared_adjacent_order_not_label_sorting() -> None:
    from app.schemas.sizing import BodyMeasurements, SizeChart, SizeRange, SizeRecommendationRequest
    from app.services.size_recommendation_service import SizeRecommendationService

    service = SizeRecommendationService()
    chart = SizeChart(
        id=2,
        name="Custom Order",
        sizes=[
            SizeRange("M", 91, 97, 73, 79, 99, 105),
            SizeRange("S", 84, 90, 66, 72, 92, 98),
            SizeRange("L", 98, 104, 80, 86, 106, 112),
        ],
    )
    result = service.recommend_size(
        SizeRecommendationRequest(
            fit_type="oversized",
            measurements=BodyMeasurements(chest_cm=94, waist_cm=76, hips_cm=102),
            size_chart=chart,
        )
    )

    assert result.base_size == "M"
    assert result.recommended_size == "S"
    assert result.confidence == "medium"
    assert "fit_adjusted_up" in result.warnings


def test_size_recommendation_keeps_base_size_when_fit_adjustment_has_no_adjacent_size() -> None:
    from app.schemas.sizing import BodyMeasurements, SizeChart, SizeRange, SizeRecommendationRequest
    from app.services.size_recommendation_service import SizeRecommendationService

    service = SizeRecommendationService()
    chart = SizeChart(
        name="Edge Sizes",
        sizes=[
            SizeRange("S", 84, 90, 66, 72, 92, 98),
            SizeRange("M", 91, 97, 73, 79, 99, 105),
        ],
    )
    result = service.recommend_size(
        SizeRecommendationRequest(
            fit_type="slim",
            measurements=BodyMeasurements(chest_cm=88, waist_cm=70, hips_cm=95),
            size_chart=chart,
        )
    )

    assert result.base_size == "S"
    assert result.recommended_size == "S"
    assert "fit_adjustment_unavailable" in result.warnings
