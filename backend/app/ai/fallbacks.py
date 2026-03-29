from __future__ import annotations


def size_explanation_fallback(*, result: dict) -> tuple[str, list[str]]:
    explanation = (
        f"The recommended size is {result['recommended_size']} based on the deterministic size chart match. "
        f"The base size was {result['base_size']} with {result['confidence']} confidence."
    )
    highlights = [
        f"Match method: {result['match_method']}",
        f"Requested fit: {result['fit_type']}",
    ]
    return explanation, highlights


def wardrobe_explanation_fallback(*, result: dict) -> tuple[str, list[str]]:
    summary = result["summary"]
    outfit_explanations = [
        outfit["explanation"]
        for outfit in result["outfits"]
    ]
    return summary, outfit_explanations


def rerank_fallback(*, candidates: list[dict], occasion: str | None) -> tuple[list[str], str]:
    ordered_ids = [candidate["candidate_id"] for candidate in candidates]
    summary = "Returned the deterministic candidate order."
    if occasion:
        summary = f"Returned the deterministic candidate order for {occasion}."
    return ordered_ids, summary


def stylist_fallback(*, occasion: str | None) -> str:
    if occasion:
        return f"These deterministic outfits are the best available matches for {occasion}."
    return "These deterministic outfits are the best available matches from the catalog."
