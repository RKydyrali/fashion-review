from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class ProviderTimeoutError(RuntimeError):
    pass


@dataclass(frozen=True)
class TryOnProviderResult:
    image_bytes: bytes
    content_type: str


class TryOnProvider(Protocol):
    def generate(
        self,
        *,
        source_image_bytes: bytes,
        source_content_type: str,
        garment_image_urls: list[str],
    ) -> tuple[bytes, str] | TryOnProviderResult: ...


class FluxTryOnProvider:
    def __init__(self, *, api_url: str | None = None) -> None:
        self.api_url = api_url

    def generate(
        self,
        *,
        source_image_bytes: bytes,
        source_content_type: str,
        garment_image_urls: list[str],
    ) -> TryOnProviderResult:
        if not self.api_url:
            raise RuntimeError("FLUX provider is not configured")

        raise RuntimeError("FLUX provider integration is not implemented in this environment")
