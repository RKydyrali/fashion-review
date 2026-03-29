from __future__ import annotations

import json


SIZE_EXPLANATION_TEMPLATE_VERSION = "size_explanation_v1"
WARDROBE_EXPLANATION_TEMPLATE_VERSION = "wardrobe_explanation_v1"
RERANK_TEMPLATE_VERSION = "outfit_rerank_v1"
STYLIST_TEMPLATE_VERSION = "stylist_v1"
TRY_ON_TEMPLATE_VERSION = "try_on_v1"
PRODUCT_TRANSLATION_TEMPLATE_VERSION = "product_translation_v1"


def size_explanation_messages(*, language: str, snapshot: dict) -> list[dict]:
    return [
        {
            "role": "system",
            "content": (
                "Return concise, factual JSON only. "
                "Do not change any deterministic decision. "
                "Explain the provided size result in plain language."
            ),
        },
        {
            "role": "user",
            "content": json.dumps(
                {
                    "language": language,
                    "deterministic_size_result": snapshot,
                },
                ensure_ascii=False,
            ),
        },
    ]


def wardrobe_explanation_messages(*, language: str, snapshot: dict, occasion: str | None, preferences: list[str]) -> list[dict]:
    return [
        {
            "role": "system",
            "content": (
                "Return concise JSON only. "
                "Do not alter the outfit list or introduce new items. "
                "Explain the provided deterministic wardrobe result."
            ),
        },
        {
            "role": "user",
            "content": json.dumps(
                {
                    "language": language,
                    "occasion": occasion,
                    "preferences": preferences,
                    "deterministic_wardrobe_result": snapshot,
                },
                ensure_ascii=False,
            ),
        },
    ]


def rerank_messages(*, language: str, snapshot: dict, occasion: str | None, preferences: list[str]) -> list[dict]:
    return [
        {
            "role": "system",
            "content": (
                "Return JSON only. "
                "Reorder only the provided candidate ids. "
                "Never introduce new ids or new items."
            ),
        },
        {
            "role": "user",
            "content": json.dumps(
                {
                    "language": language,
                    "occasion": occasion,
                    "preferences": preferences,
                    "candidates": snapshot,
                },
                ensure_ascii=False,
            ),
        },
    ]


def stylist_messages(*, language: str, snapshot: dict, occasion: str | None, preferences: list[str]) -> list[dict]:
    return [
        {
            "role": "system",
            "content": (
                "Return JSON only. "
                "Work only with the provided deterministic outfit candidates. "
                "Do not introduce new products or reorder outside the supplied candidate ids."
            ),
        },
        {
            "role": "user",
            "content": json.dumps(
                {
                    "language": language,
                    "occasion": occasion,
                    "preferences": preferences,
                    "deterministic_candidates": snapshot,
                },
                ensure_ascii=False,
            ),
        },
    ]


def product_translation_messages(*, english_copy: dict, context: dict) -> list[dict]:
    return [
        {
            "role": "system",
            "content": (
                "Return valid JSON only. "
                "Translate the provided English fashion catalog copy into natural, fluent Russian and Kazakh for a real ecommerce catalog. "
                "Do not translate word by word. Rewrite each field so it sounds native, clear, and logical to shoppers in that language while preserving the original meaning. "
                "Preserve garment facts, tone, field intent, and brand or model names such as BRIGHT. "
                "Use natural fashion phrasing, correct grammar, and culturally normal wording. "
                "Do not invent materials, colors, sizes, delivery promises, or extra marketing claims. "
                "If an English optional field is null or empty, keep it null or empty in the translations. "
                "Keep product names brand-first when natural, for example 'Футболка BRIGHT' and 'BRIGHT футболкасы'. "
                "Use localized formatting where natural, for example '95,5% хлопок' and '95,5% мақта'. "
                "For Russian and Kazakh, prefer natural ecommerce wording over literal sentence order. "
                "Terms like 'oversize' may stay borrowed when that is the most natural catalog wording."
            ),
        },
        {
            "role": "user",
            "content": json.dumps(
                {
                    "source_language": "en",
                    "target_languages": ["ru", "kk"],
                    "style_goal": {
                        "ru": "Native, polished catalog Russian. Not literal. Smooth and logical product copy.",
                        "kk": "Native, polished catalog Kazakh. Not literal. Smooth and logical product copy.",
                    },
                    "product_context": context,
                    "english_copy": english_copy,
                },
                ensure_ascii=False,
            ),
        },
    ]


def try_on_prompt(*, language: str, garments: list[dict[str, str]], fit_class: str) -> str:
    language_name = {
        "ru": "Russian",
        "kk": "Kazakh",
    }.get(language, "English")
    fit_guidance = {
        "close": "show the garment with a close fit and minimal ease",
        "regular": "show the garment with a regular fit and balanced ease",
        "relaxed": "show the garment with a relaxed fit and visible ease",
        "oversized": "show the garment with an oversized fit and generous ease",
    }[fit_class]
    garment_descriptions = ", ".join(
        f"{garment['name']} ({garment['category']})" for garment in garments
    )
    reference_phrase = "Each following image is a garment reference product photo."
    apply_phrase = f"Apply the outfit using these garments: {garment_descriptions}. {fit_guidance}."
    return (
        f"{language_name} fashion try-on render. The first image is the user's portrait. "
        f"{reference_phrase} "
        "Preserve the user's exact identity, face, hairstyle, pose, body proportions, camera angle, framing, and lighting. "
        "Edit the portrait so the person is wearing the referenced garments. Replace only the outfit appearance. "
        f"{apply_phrase} "
        "Keep the garment colors, silhouettes, and key details aligned with the reference product photos. "
        "Do not alter the person's body shape, age, skin tone, background, or pose. "
        "Keep the result realistic, retail-focused, and stable."
    )
