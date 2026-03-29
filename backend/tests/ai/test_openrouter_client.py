from app.ai.client import OpenRouterClient


def test_generate_image_requests_image_only_modality(monkeypatch) -> None:
    client = OpenRouterClient(
        api_key="test-key",
        base_url="https://openrouter.ai/api/v1",
        timeout_seconds=30,
    )
    captured_payload: dict | None = None

    def fake_post_json(path: str, payload: dict) -> dict:
        nonlocal captured_payload
        captured_payload = payload
        return {
            "images": [
                {
                    "image_base64": "aGVsbG8=",
                    "mime_type": "image/png",
                }
            ]
        }

    monkeypatch.setattr(client, "_post_json", fake_post_json)

    result = client.generate_image(
        model="black-forest-labs/flux.2-pro",
        prompt="Generate a try-on image",
        prompt_template_version="v1",
        images=[
            {
                "source": "url",
                "url": "https://example.com/product.png",
            }
        ],
        metadata={"job_id": 1},
    )

    assert result.content_type == "image/png"
    assert result.image_bytes == b"hello"
    assert captured_payload is not None
    assert captured_payload["modalities"] == ["image"]


def test_generate_image_requests_text_and_image_modalities_for_gemini(monkeypatch) -> None:
    client = OpenRouterClient(
        api_key="test-key",
        base_url="https://openrouter.ai/api/v1",
        timeout_seconds=30,
    )
    captured_payload: dict | None = None

    def fake_post_json(path: str, payload: dict) -> dict:
        nonlocal captured_payload
        captured_payload = payload
        return {
            "choices": [
                {
                    "message": {
                        "images": [
                            {
                                "image_base64": "aGVsbG8=",
                                "mime_type": "image/png",
                            }
                        ]
                    }
                }
            ]
        }

    monkeypatch.setattr(client, "_post_json", fake_post_json)

    result = client.generate_image(
        model="google/gemini-2.5-flash-image",
        prompt="Edit the portrait with the garment",
        prompt_template_version="v1",
        images=[
            {
                "source": "url",
                "url": "https://example.com/product.png",
            }
        ],
        metadata={"job_id": 2},
    )

    assert result.content_type == "image/png"
    assert result.image_bytes == b"hello"
    assert captured_payload is not None
    assert captured_payload["modalities"] == ["image", "text"]
