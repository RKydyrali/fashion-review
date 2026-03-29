from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from app.ai.client import OpenRouterClient, OpenRouterError
from app.ai.fallbacks import rerank_fallback, size_explanation_fallback, stylist_fallback, wardrobe_explanation_fallback
from app.ai.prompts import (
    PRODUCT_TRANSLATION_TEMPLATE_VERSION,
    RERANK_TEMPLATE_VERSION,
    SIZE_EXPLANATION_TEMPLATE_VERSION,
    STYLIST_TEMPLATE_VERSION,
    WARDROBE_EXPLANATION_TEMPLATE_VERSION,
    product_translation_messages,
    rerank_messages,
    size_explanation_messages,
    stylist_messages,
    wardrobe_explanation_messages,
)
from app.core.config import get_settings
from app.repositories.ai_call_repository import AICallRepository
from app.schemas.ai import (
    AIOutfitRerankResponse,
    AIProductTranslationMap,
    AIProductTranslationResponse,
    AISizeExplanationResponse,
    AIStylistResponse,
    AIWardrobeExplanationResponse,
)


class _SizeExplanationOutput(BaseModel):
    explanation: str
    highlights: list[str]


class _WardrobeExplanationOutput(BaseModel):
    summary: str
    outfit_explanations: list[str]


class _RerankOutput(BaseModel):
    ordered_candidate_ids: list[str]
    summary: str


class _StylistOutput(BaseModel):
    ordered_candidate_ids: list[str]
    stylist_note: str


class _ProductTranslationContent(BaseModel):
    name: str
    description: str | None = None
    subtitle: str | None = None
    long_description: str | None = None
    fabric_notes: str | None = None
    care_notes: str | None = None
    preorder_note: str | None = None
    display_category: str


class _ProductTranslationOutput(BaseModel):
    ru: _ProductTranslationContent
    kk: _ProductTranslationContent


class AITextService:
    def __init__(self, *, openrouter_client: OpenRouterClient, call_repository: AICallRepository | None = None) -> None:
        self.openrouter_client = openrouter_client
        self.call_repository = call_repository
        self.settings = get_settings()

    def explain_size(self, *, deterministic_result: dict, language: str, user_id: int | None = None) -> AISizeExplanationResponse:
        fallback_explanation, fallback_highlights = size_explanation_fallback(result=deterministic_result)
        metadata, parsed = self._maybe_generate(
            feature_name="size_explanations",
            enabled=self.settings.ai_enabled and self.settings.ai_size_explanations_enabled,
            prompt_template_version=SIZE_EXPLANATION_TEMPLATE_VERSION,
            request_payload={"language": language, "deterministic_result": deterministic_result},
            response_model=_SizeExplanationOutput,
            messages=size_explanation_messages(language=language, snapshot=deterministic_result),
            user_id=user_id,
        )
        if parsed is None:
            return AISizeExplanationResponse(
                deterministic_result=deterministic_result,
                explanation=fallback_explanation,
                highlights=fallback_highlights,
                **metadata,
            )

        return AISizeExplanationResponse(
            deterministic_result=deterministic_result,
            explanation=parsed.explanation,
            highlights=parsed.highlights,
            **metadata,
        )

    def explain_wardrobe(
        self,
        *,
        deterministic_result: dict,
        language: str,
        occasion: str | None,
        preferences: list[str],
        user_id: int | None = None,
    ) -> AIWardrobeExplanationResponse:
        fallback_summary, fallback_outfits = wardrobe_explanation_fallback(result=deterministic_result)
        metadata, parsed = self._maybe_generate(
            feature_name="wardrobe_explanations",
            enabled=self.settings.ai_enabled and self.settings.ai_capsule_explanations_enabled,
            prompt_template_version=WARDROBE_EXPLANATION_TEMPLATE_VERSION,
            request_payload={"language": language, "occasion": occasion, "preferences": preferences, "deterministic_result": deterministic_result},
            response_model=_WardrobeExplanationOutput,
            messages=wardrobe_explanation_messages(language=language, snapshot=deterministic_result, occasion=occasion, preferences=preferences),
            user_id=user_id,
        )
        if parsed is None:
            return AIWardrobeExplanationResponse(
                deterministic_result=deterministic_result,
                summary=fallback_summary,
                outfit_explanations=fallback_outfits,
                **metadata,
            )

        return AIWardrobeExplanationResponse(
            deterministic_result=deterministic_result,
            summary=parsed.summary,
            outfit_explanations=parsed.outfit_explanations,
            **metadata,
        )

    def rerank_candidates(
        self,
        *,
        candidates: list[dict[str, Any]],
        language: str,
        occasion: str | None,
        preferences: list[str],
        user_id: int | None = None,
    ) -> AIOutfitRerankResponse:
        fallback_ids, fallback_summary = rerank_fallback(candidates=candidates, occasion=occasion)
        metadata, parsed = self._maybe_generate(
            feature_name="outfit_rerank",
            enabled=self.settings.ai_enabled and self.settings.ai_outfit_rerank_enabled,
            prompt_template_version=RERANK_TEMPLATE_VERSION,
            request_payload={"language": language, "occasion": occasion, "preferences": preferences, "candidates": candidates},
            response_model=_RerankOutput,
            messages=rerank_messages(language=language, snapshot=candidates, occasion=occasion, preferences=preferences),
            user_id=user_id,
        )
        ordered_ids = fallback_ids
        summary = fallback_summary
        if parsed is not None:
            known_ids = [candidate["candidate_id"] for candidate in candidates]
            returned_ids = parsed.ordered_candidate_ids
            if sorted(returned_ids) == sorted(known_ids) and len(returned_ids) == len(known_ids):
                ordered_ids = returned_ids
                summary = parsed.summary
                metadata = {**metadata, "ai_status": "completed", "used_fallback": False, "error_message": None}
            else:
                metadata = {**metadata, "ai_status": "fallback", "used_fallback": True, "error_message": "AI returned invalid candidate ids"}

        reranked_candidates = sorted(candidates, key=lambda candidate: ordered_ids.index(candidate["candidate_id"]))
        return AIOutfitRerankResponse(
            deterministic_candidates=candidates,
            reranked_candidates=reranked_candidates,
            ordered_candidate_ids=ordered_ids,
            summary=summary,
            **metadata,
        )

    def style_candidates(
        self,
        *,
        deterministic_result: dict,
        candidates: list[dict[str, Any]],
        language: str,
        occasion: str | None,
        preferences: list[str],
        user_id: int | None = None,
    ) -> AIStylistResponse:
        rerank_result = self.rerank_candidates(
            candidates=candidates,
            language=language,
            occasion=occasion,
            preferences=preferences,
            user_id=user_id,
        )
        metadata, parsed = self._maybe_generate(
            feature_name="stylist",
            enabled=self.settings.ai_enabled and self.settings.ai_stylist_enabled,
            prompt_template_version=STYLIST_TEMPLATE_VERSION,
            request_payload={"language": language, "occasion": occasion, "preferences": preferences, "candidates": candidates},
            response_model=_StylistOutput,
            messages=stylist_messages(language=language, snapshot=candidates, occasion=occasion, preferences=preferences),
            user_id=user_id,
        )

        stylist_note = stylist_fallback(occasion=occasion)
        if parsed is not None and parsed.ordered_candidate_ids == rerank_result.ordered_candidate_ids:
            stylist_note = parsed.stylist_note
            metadata = {**metadata, "ai_status": "completed", "used_fallback": rerank_result.used_fallback and metadata["used_fallback"], "error_message": None}
        else:
            metadata = {**metadata, "ai_status": rerank_result.ai_status, "used_fallback": True, "error_message": rerank_result.error_message}

        return AIStylistResponse(
            deterministic_result=deterministic_result,
            deterministic_candidates=rerank_result.deterministic_candidates,
            recommended_candidates=rerank_result.reranked_candidates,
            ordered_candidate_ids=rerank_result.ordered_candidate_ids,
            stylist_note=stylist_note,
            **metadata,
        )

    def translate_product_copy_from_english(
        self,
        *,
        english_copy: dict[str, Any],
        normalized_category: str | None,
        color: str | None,
        season_tags: list[str],
        user_id: int | None = None,
    ) -> AIProductTranslationResponse:
        metadata, parsed = self._maybe_generate(
            feature_name="product_translation",
            enabled=self.settings.ai_enabled,
            prompt_template_version=PRODUCT_TRANSLATION_TEMPLATE_VERSION,
            request_payload={
                "english_copy": english_copy,
                "normalized_category": normalized_category,
                "color": color,
                "season_tags": season_tags,
            },
            response_model=_ProductTranslationOutput,
            messages=product_translation_messages(
                english_copy=english_copy,
                context={
                    "normalized_category": normalized_category,
                    "color": color,
                    "season_tags": season_tags,
                },
            ),
            user_id=user_id,
        )
        return AIProductTranslationResponse(
            translations=(AIProductTranslationMap.model_validate(parsed.model_dump()) if parsed is not None else None),
            **metadata,
        )

    def _maybe_generate(
        self,
        *,
        feature_name: str,
        enabled: bool,
        prompt_template_version: str,
        request_payload: dict,
        response_model: type[BaseModel],
        messages: list[dict],
        user_id: int | None,
    ) -> tuple[dict[str, Any], BaseModel | None]:
        disabled_metadata = {
            "ai_status": "disabled",
            "provider_name": None,
            "model_name": None,
            "prompt_template_version": prompt_template_version,
            "used_fallback": True,
            "error_message": None,
        }
        if not enabled:
            return disabled_metadata, None

        if hasattr(self.openrouter_client, "is_configured") and not self.openrouter_client.is_configured():
            return {**disabled_metadata, "ai_status": "fallback", "error_message": "OpenRouter is not configured"}, None

        try:
            result = self.openrouter_client.generate_structured(
                model=self.settings.ai_text_model,
                messages=messages,
                prompt_template_version=prompt_template_version,
                response_schema_name=f"{feature_name}_response",
                response_schema=response_model.model_json_schema(),
                temperature=self.settings.ai_text_temperature,
                top_p=self.settings.ai_text_top_p,
            )
            parsed = response_model.model_validate(result.parsed_output)
            self._record_call(
                feature_name=feature_name,
                user_id=user_id,
                prompt_template_version=prompt_template_version,
                request_payload=request_payload,
                response_payload=result.raw_response,
                status="completed",
                provider_name=result.provider_name,
                model_name=result.model_name,
                latency_ms=result.latency_ms,
                error_message=None,
                error_metadata=None,
            )
            return {
                "ai_status": "completed",
                "provider_name": result.provider_name,
                "model_name": result.model_name,
                "prompt_template_version": prompt_template_version,
                "used_fallback": False,
                "error_message": None,
            }, parsed
        except (OpenRouterError, ValueError, AttributeError) as exc:
            self._record_call(
                feature_name=feature_name,
                user_id=user_id,
                prompt_template_version=prompt_template_version,
                request_payload=request_payload,
                response_payload=None,
                status="failed",
                provider_name="openrouter",
                model_name=self.settings.ai_text_model,
                latency_ms=None,
                error_message=str(exc),
                error_metadata={"exception": exc.__class__.__name__},
            )
            return {
                "ai_status": "fallback",
                "provider_name": "openrouter",
                "model_name": self.settings.ai_text_model,
                "prompt_template_version": prompt_template_version,
                "used_fallback": True,
                "error_message": str(exc),
            }, None

    def _record_call(
        self,
        *,
        feature_name: str,
        user_id: int | None,
        prompt_template_version: str,
        request_payload: dict,
        response_payload: dict | None,
        status: str,
        provider_name: str,
        model_name: str,
        latency_ms: int | None,
        error_message: str | None,
        error_metadata: dict | None,
    ) -> None:
        if self.call_repository is None:
            return None
        self.call_repository.create(
            user_id=user_id,
            feature_name=feature_name,
            provider_name=provider_name,
            model_name=model_name,
            prompt_template_version=prompt_template_version,
            status=status,
            latency_ms=latency_ms,
            request_payload=request_payload,
            response_payload=response_payload,
            error_metadata=error_metadata,
            error_message=error_message,
            related_resource_type=None,
            related_resource_id=None,
        )
        return None
