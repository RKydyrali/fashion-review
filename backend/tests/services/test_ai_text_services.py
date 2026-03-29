def test_ai_outfit_rerank_service_falls_back_when_model_returns_unknown_candidate_ids() -> None:
    from app.ai.text_service import AITextService
    from app.core.config import get_settings

    class _InvalidClient:
        def generate_structured(self, **kwargs):
            return {
                "provider_name": "openrouter",
                "model_name": "arcee-ai/trinity-large-preview:free",
                "prompt_template_version": kwargs["prompt_template_version"],
                "latency_ms": 8,
                "parsed_output": {
                    "ordered_candidate_ids": ["unknown-look"],
                    "summary": "bad output",
                },
                "raw_response": {"ok": True},
            }

    settings = get_settings()
    settings.ai_enabled = True
    settings.ai_outfit_rerank_enabled = True

    service = AITextService(openrouter_client=_InvalidClient())
    result = service.rerank_candidates(
        candidates=[
            {
                "candidate_id": "look-1",
                "colors": ["white", "beige"],
                "items": [{"id": 1, "sku": "TOP-001", "name": "Top"}],
            },
            {
                "candidate_id": "look-2",
                "colors": ["black"],
                "items": [{"id": 2, "sku": "BOT-001", "name": "Bottom"}],
            },
        ],
        language="en",
        occasion="work",
        preferences=["minimal"],
    )

    assert result.ai_status == "fallback"
    assert result.used_fallback is True
    assert result.ordered_candidate_ids == ["look-1", "look-2"]
    assert [candidate["candidate_id"] for candidate in result.reranked_candidates] == ["look-1", "look-2"]
