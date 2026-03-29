from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

from app.schemas.sizing import SizeRecommendationRequest, SizeRecommendationResponse
from app.schemas.wardrobe import CapsuleWardrobeRequest, CapsuleWardrobeResponse, WardrobeCatalogItemInput, WardrobeItemRead

AIStatus = Literal["completed", "fallback", "disabled"]


class AIResponseBase(BaseModel):
    ai_status: AIStatus
    provider_name: str | None
    model_name: str | None
    prompt_template_version: str
    used_fallback: bool
    error_message: str | None = None


class AISizeExplanationRequest(SizeRecommendationRequest):
    pass


class AISizeExplanationResponse(AIResponseBase):
    deterministic_result: dict[str, Any] | SizeRecommendationResponse
    explanation: str
    highlights: list[str]


class AIWardrobeExplanationRequest(CapsuleWardrobeRequest):
    occasion: str | None = None
    preferences: list[str] = Field(default_factory=list)


class AIWardrobeExplanationResponse(AIResponseBase):
    deterministic_result: dict[str, Any] | CapsuleWardrobeResponse
    summary: str
    outfit_explanations: list[str]


class AIOutfitCandidateInput(BaseModel):
    candidate_id: str
    items: list[WardrobeItemRead | dict[str, Any]]
    colors: list[str]
    explanation: str | None = None


class AIOutfitRerankRequest(BaseModel):
    candidates: list[AIOutfitCandidateInput] = Field(min_length=1)
    occasion: str | None = None
    preferences: list[str] = Field(default_factory=list)


class AIOutfitRerankResponse(AIResponseBase):
    deterministic_candidates: list[dict[str, Any]]
    reranked_candidates: list[dict[str, Any]]
    ordered_candidate_ids: list[str]
    summary: str


class AIStylistRequest(BaseModel):
    season: str
    occasion: str | None = None
    preferences: list[str] = Field(default_factory=list)
    max_outfits: int = Field(default=4, ge=1, le=8)
    target_item_limit: int = Field(default=6, ge=3, le=12)
    catalog: list[WardrobeCatalogItemInput] | None = None


class AIStylistResponse(AIResponseBase):
    deterministic_result: dict[str, Any] | CapsuleWardrobeResponse
    deterministic_candidates: list[dict[str, Any]]
    recommended_candidates: list[dict[str, Any]]
    ordered_candidate_ids: list[str]
    stylist_note: str


class AIProductTranslationContent(BaseModel):
    name: str
    description: str | None = None
    subtitle: str | None = None
    long_description: str | None = None
    fabric_notes: str | None = None
    care_notes: str | None = None
    preorder_note: str | None = None
    display_category: str


class AIProductTranslationMap(BaseModel):
    ru: AIProductTranslationContent
    kk: AIProductTranslationContent


class AIProductTranslationResponse(AIResponseBase):
    translations: AIProductTranslationMap | None = None


class AITryOnJobRead(AIResponseBase):
    id: int
    status: str
    product_id: int
    fit_class: str
    fit_reason: str
    source_image_url: str
    result_image_url: str | None
    primary_model_name: str
    fallback_model_name: str
    selected_model_name: str | None
    created_at: datetime
    updated_at: datetime


class AITryOnBodyMeasurementsInput(BaseModel):
    chest_cm: float | None = Field(default=None, gt=0)
    waist_cm: float | None = Field(default=None, gt=0)
    hips_cm: float | None = Field(default=None, gt=0)

    @model_validator(mode="after")
    def require_all_or_none(self) -> "AITryOnBodyMeasurementsInput":
        values = [self.chest_cm, self.waist_cm, self.hips_cm]
        if any(value is not None for value in values) and any(value is None for value in values):
            raise ValueError("body measurements must include chest_cm, waist_cm, and hips_cm together")
        return self
