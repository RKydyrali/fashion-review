from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from app.api.deps import (
    CurrentUser,
    RequestLanguage,
    get_ai_text_service,
    get_ai_try_on_job_service,
    get_ai_try_on_worker_service,
    get_size_recommendation_service,
    get_wardrobe_service,
)
from app.schemas.ai import (
    AIOutfitCandidateInput,
    AIOutfitRerankRequest,
    AIOutfitRerankResponse,
    AISizeExplanationRequest,
    AISizeExplanationResponse,
    AIStylistRequest,
    AIStylistResponse,
    AITryOnJobRead,
    AIWardrobeExplanationRequest,
    AIWardrobeExplanationResponse,
)
from app.schemas.sizing import BodyMeasurements
from app.schemas.wardrobe import CapsuleWardrobeRequest
from app.services.size_recommendation_service import SizeRecommendationService
from app.services.wardrobe_service import WardrobeService
from app.ai.text_service import AITextService
from app.ai.try_on_service import AITryOnJobService
from app.ai.try_on_worker_service import AITryOnWorkerService

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/sizes/explanations", response_model=AISizeExplanationResponse)
def explain_size(
    payload: AISizeExplanationRequest,
    current_user: CurrentUser,
    language: RequestLanguage,
    size_service: Annotated[SizeRecommendationService, Depends(get_size_recommendation_service)],
    ai_service: Annotated[AITextService, Depends(get_ai_text_service)],
) -> AISizeExplanationResponse:
    measurements = payload.measurements
    if measurements is None and current_user.body_profile is not None:
        measurements = current_user.body_profile.to_body_measurements()
    deterministic_result = size_service.recommend_size(
        payload.model_copy(update={"measurements": measurements})
    )
    return ai_service.explain_size(
        deterministic_result=deterministic_result.model_dump(mode="json"),
        language=language.value,
        user_id=current_user.id,
    )


@router.post("/wardrobes/explanations", response_model=AIWardrobeExplanationResponse)
def explain_wardrobe(
    payload: AIWardrobeExplanationRequest,
    current_user: CurrentUser,
    language: RequestLanguage,
    wardrobe_service: Annotated[WardrobeService, Depends(get_wardrobe_service)],
    ai_service: Annotated[AITextService, Depends(get_ai_text_service)],
) -> AIWardrobeExplanationResponse:
    deterministic_result = wardrobe_service.generate_capsule(
        CapsuleWardrobeRequest(
            season=payload.season,
            allowed_categories=payload.allowed_categories,
            max_outfits=payload.max_outfits,
            target_item_limit=payload.target_item_limit,
            catalog=payload.catalog,
        ),
        language=language,
    )
    return ai_service.explain_wardrobe(
        deterministic_result=deterministic_result.model_dump(mode="json"),
        language=language.value,
        occasion=payload.occasion,
        preferences=payload.preferences,
        user_id=current_user.id,
    )


@router.post("/outfits/rerank", response_model=AIOutfitRerankResponse)
def rerank_outfits(
    payload: AIOutfitRerankRequest,
    current_user: CurrentUser,
    language: RequestLanguage,
    ai_service: Annotated[AITextService, Depends(get_ai_text_service)],
) -> AIOutfitRerankResponse:
    candidates = [candidate.model_dump(mode="json") for candidate in payload.candidates]
    return ai_service.rerank_candidates(
        candidates=candidates,
        language=language.value,
        occasion=payload.occasion,
        preferences=payload.preferences,
        user_id=current_user.id,
    )


@router.post("/stylist/recommendations", response_model=AIStylistResponse)
def stylist_recommendations(
    payload: AIStylistRequest,
    current_user: CurrentUser,
    language: RequestLanguage,
    wardrobe_service: Annotated[WardrobeService, Depends(get_wardrobe_service)],
    ai_service: Annotated[AITextService, Depends(get_ai_text_service)],
) -> AIStylistResponse:
    deterministic_result = wardrobe_service.generate_capsule(
        CapsuleWardrobeRequest(
            season=payload.season,
            max_outfits=payload.max_outfits,
            target_item_limit=payload.target_item_limit,
            catalog=payload.catalog,
        ),
        language=language,
    )
    candidates = _build_candidate_payloads(deterministic_result.outfits)
    return ai_service.style_candidates(
        deterministic_result=deterministic_result.model_dump(mode="json"),
        candidates=candidates,
        language=language.value,
        occasion=payload.occasion,
        preferences=payload.preferences,
        user_id=current_user.id,
    )


@router.post("/try-on/jobs", response_model=AITryOnJobRead)
def create_ai_try_on_job(
    current_user: CurrentUser,
    service: Annotated[AITryOnJobService, Depends(get_ai_try_on_job_service)],
    worker_service: Annotated[AITryOnWorkerService, Depends(get_ai_try_on_worker_service)],
    user_image: UploadFile = File(...),
    product_id: int | None = Form(default=None),
    product_ids: list[int] | None = Form(default=None),
    chest_cm: float | None = Form(default=None),
    waist_cm: float | None = Form(default=None),
    hips_cm: float | None = Form(default=None),
    preferred_fit: str | None = Form(default=None),
    chart_id: int | None = Form(default=None),
    product_chest_cm: float | None = Form(default=None),
    product_waist_cm: float | None = Form(default=None),
    product_hips_cm: float | None = Form(default=None),
) -> AITryOnJobRead:
    selected_product_ids = product_ids or ([product_id] if product_id is not None else None)
    if not selected_product_ids:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="At least one product must be selected for try-on")

    body_measurements = _resolve_body_measurements(
        current_user=current_user,
        chest_cm=chest_cm,
        waist_cm=waist_cm,
        hips_cm=hips_cm,
    )
    product_measurements = _resolve_product_measurements(
        chest_cm=product_chest_cm,
        waist_cm=product_waist_cm,
        hips_cm=product_hips_cm,
    )
    job = service.create_job_from_upload(
        user_id=current_user.id,
        product_id=selected_product_ids[0],
        style_product_ids=selected_product_ids,
        upload=user_image,
        body_measurements=body_measurements,
        product_measurements=product_measurements,
        preferred_fit=preferred_fit or (current_user.body_profile.preferred_fit if current_user.body_profile else None),
        chart_id=chart_id,
    )
    processed_job = worker_service.process_job(job.id)
    return processed_job or job


@router.get("/try-on/jobs/{job_id}", response_model=AITryOnJobRead)
def get_ai_try_on_job(
    job_id: int,
    current_user: CurrentUser,
    service: Annotated[AITryOnJobService, Depends(get_ai_try_on_job_service)],
) -> AITryOnJobRead:
    return service.get_job(user_id=current_user.id, job_id=job_id)


def _build_candidate_payloads(outfits) -> list[dict]:
    candidates: list[dict] = []
    for index, outfit in enumerate(outfits, start=1):
        candidates.append(
            AIOutfitCandidateInput(
                candidate_id=f"look-{index}",
                items=[item.model_dump(mode="json") for item in outfit.items],
                colors=list(outfit.colors),
                explanation=outfit.explanation,
            ).model_dump(mode="json")
        )
    return candidates


def _resolve_body_measurements(*, current_user, chest_cm: float | None, waist_cm: float | None, hips_cm: float | None) -> dict | None:
    if chest_cm is not None and waist_cm is not None and hips_cm is not None:
        return BodyMeasurements(chest_cm=chest_cm, waist_cm=waist_cm, hips_cm=hips_cm).model_dump(mode="json")
    if current_user.body_profile is not None:
        body_measurements = current_user.body_profile.to_body_measurements()
        if body_measurements is not None:
            return body_measurements.model_dump(mode="json")
    return None


def _resolve_product_measurements(*, chest_cm: float | None, waist_cm: float | None, hips_cm: float | None) -> dict | None:
    if chest_cm is None and waist_cm is None and hips_cm is None:
        return None
    payload = {}
    if chest_cm is not None:
        payload["chest_cm"] = chest_cm
    if waist_cm is not None:
        payload["waist_cm"] = waist_cm
    if hips_cm is not None:
        payload["hips_cm"] = hips_cm
    return payload
