from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

FitType = Literal["regular", "oversized", "slim"]
ConfidenceLevel = Literal["high", "medium", "low"]
MatchMethod = Literal["exact_range", "closest_distance"]


class BodyMeasurements(BaseModel):
    chest_cm: float = Field(gt=0)
    waist_cm: float = Field(gt=0)
    hips_cm: float = Field(gt=0)


class SizeRange(BaseModel):
    size_label: str
    chest_min_cm: float
    chest_max_cm: float
    waist_min_cm: float
    waist_max_cm: float
    hips_min_cm: float
    hips_max_cm: float

    def __init__(self, *args, **kwargs) -> None:
        if args:
            kwargs = {
                "size_label": args[0],
                "chest_min_cm": args[1],
                "chest_max_cm": args[2],
                "waist_min_cm": args[3],
                "waist_max_cm": args[4],
                "hips_min_cm": args[5],
                "hips_max_cm": args[6],
                **kwargs,
            }
        super().__init__(**kwargs)

    @model_validator(mode="after")
    def validate_bounds(self) -> "SizeRange":
        for minimum, maximum, label in (
            (self.chest_min_cm, self.chest_max_cm, "chest"),
            (self.waist_min_cm, self.waist_max_cm, "waist"),
            (self.hips_min_cm, self.hips_max_cm, "hips"),
        ):
            if minimum > maximum:
                raise ValueError(f"{label} min must be less than or equal to max")
        return self


class SizeChart(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int | None = None
    name: str
    sizes: list[SizeRange] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_size_labels(self) -> "SizeChart":
        labels = [size.size_label for size in self.sizes]
        if len(set(labels)) != len(labels):
            raise ValueError("size labels must be unique")
        return self


class SizeRecommendationRequest(BaseModel):
    chart_id: int | None = None
    size_chart: SizeChart | None = None
    fit_type: FitType
    measurements: BodyMeasurements | None = None

    @model_validator(mode="after")
    def validate_chart_source(self) -> "SizeRecommendationRequest":
        provided_sources = int(self.chart_id is not None) + int(self.size_chart is not None)
        if provided_sources != 1:
            raise ValueError("exactly one of chart_id or size_chart must be provided")
        return self


class SizeRecommendationResponse(BaseModel):
    recommended_size: str
    base_size: str
    confidence: ConfidenceLevel
    confidence_score: float
    match_method: MatchMethod
    fit_type: FitType
    warnings: list[str]
    matched_sizes_by_measurement: dict[str, str | None]
