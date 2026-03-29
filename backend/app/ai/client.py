from __future__ import annotations

import base64
import json
import time
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class OpenRouterError(RuntimeError):
    pass


@dataclass(frozen=True)
class OpenRouterStructuredResult:
    provider_name: str
    model_name: str
    prompt_template_version: str
    latency_ms: int
    parsed_output: dict
    raw_response: dict


@dataclass(frozen=True)
class OpenRouterImageResult:
    provider_name: str
    model_name: str
    prompt_template_version: str
    latency_ms: int
    image_bytes: bytes
    content_type: str
    raw_response: dict


class OpenRouterClient:
    def __init__(self, *, api_key: str | None, base_url: str, timeout_seconds: int) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    def is_configured(self) -> bool:
        return bool(self.api_key)

    def generate_structured(
        self,
        *,
        model: str,
        messages: list[dict],
        prompt_template_version: str,
        response_schema_name: str,
        response_schema: dict,
        temperature: float,
        top_p: float,
    ) -> OpenRouterStructuredResult:
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "top_p": top_p,
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": response_schema_name,
                    "strict": True,
                    "schema": response_schema,
                },
            },
        }
        started = time.monotonic()
        response = self._post_json("/chat/completions", payload)
        latency_ms = int((time.monotonic() - started) * 1000)
        content = self._extract_text_content(response)
        try:
            parsed_output = json.loads(content)
        except json.JSONDecodeError as exc:
            raise OpenRouterError("OpenRouter returned invalid JSON content") from exc
        return OpenRouterStructuredResult(
            provider_name="openrouter",
            model_name=model,
            prompt_template_version=prompt_template_version,
            latency_ms=latency_ms,
            parsed_output=parsed_output,
            raw_response=response,
        )

    def generate_image(
        self,
        *,
        model: str,
        prompt: str,
        prompt_template_version: str,
        images: list[dict],
        metadata: dict,
    ) -> OpenRouterImageResult:
        content_items: list[dict] = [{"type": "text", "text": prompt}]
        for image in images:
            if image["source"] == "url":
                content_items.append(
                    {
                        "type": "image_url",
                        "image_url": {"url": image["url"]},
                    }
                )
                continue
            encoded = base64.b64encode(image["bytes"]).decode("ascii")
            content_items.append(
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{image['content_type']};base64,{encoded}",
                    },
                }
            )

        payload = {
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": content_items,
                }
            ],
            "modalities": self._image_modalities_for_model(model),
            "metadata": metadata,
        }
        started = time.monotonic()
        response = self._post_json("/chat/completions", payload)
        latency_ms = int((time.monotonic() - started) * 1000)
        image_bytes, content_type = self._extract_image_payload(response)
        return OpenRouterImageResult(
            provider_name="openrouter",
            model_name=model,
            prompt_template_version=prompt_template_version,
            latency_ms=latency_ms,
            image_bytes=image_bytes,
            content_type=content_type,
            raw_response=response,
        )

    def _post_json(self, path: str, payload: dict) -> dict:
        if not self.api_key:
            raise OpenRouterError("OpenRouter is not configured")

        request = Request(
            f"{self.base_url}{path}",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            body = exc.read().decode("utf-8", errors="ignore")
            raise OpenRouterError(f"OpenRouter request failed: {exc.code} {body}") from exc
        except URLError as exc:
            raise OpenRouterError("OpenRouter request failed") from exc

    def _extract_text_content(self, response: dict) -> str:
        choices = response.get("choices") or []
        if not choices:
            raise OpenRouterError("OpenRouter returned no choices")
        message = choices[0].get("message") or {}
        content = message.get("content")
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            text_parts = [
                item.get("text", "")
                for item in content
                if isinstance(item, dict) and item.get("type") == "text"
            ]
            joined = "".join(text_parts).strip()
            if joined:
                return joined
        raise OpenRouterError("OpenRouter returned no text content")

    def _extract_image_payload(self, response: dict) -> tuple[bytes, str]:
        images = response.get("images")
        if isinstance(images, list) and images:
            extracted = self._decode_image_entry(images[0])
            if extracted is not None:
                return extracted

        choices = response.get("choices") or []
        if choices:
            message = choices[0].get("message") or {}
            message_images = message.get("images")
            if isinstance(message_images, list) and message_images:
                extracted = self._decode_image_entry(message_images[0])
                if extracted is not None:
                    return extracted
            for item in message.get("content") or []:
                if not isinstance(item, dict):
                    continue
                extracted = self._decode_image_entry(item)
                if extracted is not None:
                    return extracted
        raise OpenRouterError("OpenRouter returned no image payload")

    def _decode_image_entry(self, image: dict) -> tuple[bytes, str] | None:
        image_b64 = image.get("image_base64") or image.get("b64_json")
        if image_b64:
            return base64.b64decode(image_b64), image.get("mime_type", "image/png")
        image_url = image.get("image_url")
        if isinstance(image_url, dict):
            url = image_url.get("url", "")
            if isinstance(url, str) and url.startswith("data:") and ";base64," in url:
                header, encoded = url.split(";base64,", 1)
                content_type = header.removeprefix("data:") or "image/png"
                return base64.b64decode(encoded), content_type
        return None

    def _image_modalities_for_model(self, model: str) -> list[str]:
        if model.startswith("google/gemini-"):
            return ["image", "text"]
        return ["image"]
