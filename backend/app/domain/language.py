from __future__ import annotations

from enum import StrEnum


class LanguageCode(StrEnum):
    RU = "ru"
    KK = "kk"
    EN = "en"


DEFAULT_LANGUAGE = LanguageCode.RU
SUPPORTED_LANGUAGES = {language.value for language in LanguageCode}


def parse_accept_language(header_value: str | None) -> LanguageCode | None:
    if not header_value:
        return None

    for item in header_value.split(","):
        candidate = item.split(";", 1)[0].strip().casefold()
        if not candidate:
            continue
        base_tag = candidate.split("-", 1)[0].split("_", 1)[0]
        if base_tag in SUPPORTED_LANGUAGES:
            return LanguageCode(base_tag)
    return None


def coerce_language(value: str | LanguageCode | None) -> LanguageCode | None:
    if value is None:
        return None
    if isinstance(value, LanguageCode):
        return value

    normalized = value.strip().casefold()
    if normalized in SUPPORTED_LANGUAGES:
        return LanguageCode(normalized)
    return None
