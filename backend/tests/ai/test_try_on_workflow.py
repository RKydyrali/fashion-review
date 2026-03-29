from app.ai.deterministic import build_ai_try_on_idempotency_key
from app.services.media_storage_service import LocalMediaStorageService


PNG_BYTES = b"\x89PNG\r\n\x1a\n" + (b"0" * 16)


def test_ai_try_on_idempotency_key_changes_when_primary_model_changes() -> None:
    gemini_key = build_ai_try_on_idempotency_key(
        PNG_BYTES,
        7,
        "regular",
        primary_model_name="google/gemini-2.5-flash-image",
        prompt_template_version="try_on_v1",
    )
    flux_key = build_ai_try_on_idempotency_key(
        PNG_BYTES,
        7,
        "regular",
        primary_model_name="black-forest-labs/flux.2-pro",
        prompt_template_version="try_on_v1",
    )

    assert gemini_key != flux_key


def test_media_storage_resolves_local_media_relative_path_from_url(tmp_path) -> None:
    storage = LocalMediaStorageService(tmp_path, "/media")

    assert storage.relative_path_from_url("/media/catalog/products/reference-image/file.png") == "catalog/products/reference-image/file.png"
    assert (
        storage.relative_path_from_url("http://127.0.0.1:8000/media/catalog/products/reference-image/file.png")
        == "catalog/products/reference-image/file.png"
    )
