from pathlib import Path


PNG_BYTES = b"\x89PNG\r\n\x1a\n" + (b"0" * 64)


class _PrimaryFailureClient:
    def __init__(self, *, primary_model: str) -> None:
        self.image_models: list[str] = []
        self.primary_model = primary_model

    def generate_image(self, *, model: str, prompt: str, prompt_template_version: str, images: list[dict], metadata: dict) -> dict:
        self.image_models.append(model)
        if model == self.primary_model:
            raise RuntimeError("primary model failed")
        return {
            "image_bytes": b"rendered-ai-image",
            "content_type": "image/png",
            "provider_name": "openrouter",
            "model_name": model,
            "prompt_template_version": prompt_template_version,
            "latency_ms": 12,
            "raw_response": {"ok": True},
        }


class _MultiProductClient:
    def __init__(self) -> None:
        self.last_model: str | None = None
        self.last_images: list[dict] = []
        self.last_metadata: dict = {}
        self.last_prompt: str = ""

    def generate_image(self, *, model: str, prompt: str, prompt_template_version: str, images: list[dict], metadata: dict) -> dict:
        self.last_model = model
        self.last_images = images
        self.last_metadata = metadata
        self.last_prompt = prompt
        return {
            "image_bytes": b"rendered-multi-product-image",
            "content_type": "image/png",
            "provider_name": "openrouter",
            "model_name": model,
            "prompt_template_version": prompt_template_version,
            "latency_ms": 18,
            "raw_response": {"ok": True},
        }


def test_ai_try_on_worker_uses_fallback_model_after_primary_failure(tmp_path: Path) -> None:
    from app.ai.try_on_service import AITryOnJobService
    from app.ai.try_on_worker_service import AITryOnWorkerService
    from app.core.config import get_settings
    from app.core.database import SessionLocal, initialize_database, seed_demo_catalog, seed_demo_size_charts, seed_demo_users
    from app.services.media_storage_service import LocalMediaStorageService

    initialize_database(reset=True)
    seed_demo_users()
    seed_demo_catalog()
    seed_demo_size_charts()

    settings = get_settings()
    settings.ai_enabled = True
    settings.ai_try_on_enabled = True
    settings.ai_try_on_primary_model = "google/gemini-2.5-flash-image"
    settings.ai_try_on_fallback_model = "black-forest-labs/flux.2-flex"

    client = _PrimaryFailureClient(primary_model=settings.ai_try_on_primary_model)
    storage = LocalMediaStorageService(tmp_path, "/media")

    with SessionLocal() as session:
        service = AITryOnJobService(
            session,
            openrouter_client=client,
            media_storage=storage,
        )
        job = service.create_job_from_bytes(
            user_id=1,
            product_id=1,
            image_bytes=PNG_BYTES,
            filename="person.png",
            content_type="image/png",
            body_measurements={"chest_cm": 94.0, "waist_cm": 76.0, "hips_cm": 102.0},
        )

        worker = AITryOnWorkerService(
            session,
            openrouter_client=client,
            media_storage=storage,
        )
        processed = worker.process_job(job.id)

    assert processed is not None
    assert processed.status == "completed"
    assert processed.fit_class == "regular"
    assert processed.selected_model_name == settings.ai_try_on_fallback_model
    assert client.image_models == [
        settings.ai_try_on_primary_model,
        settings.ai_try_on_fallback_model,
    ]


def test_ai_try_on_worker_uses_all_selected_products_with_current_image_model(tmp_path: Path) -> None:
    from app.ai.try_on_service import AITryOnJobService
    from app.ai.try_on_worker_service import AITryOnWorkerService
    from app.core.config import get_settings
    from app.core.database import SessionLocal, initialize_database, seed_demo_catalog, seed_demo_size_charts, seed_demo_users
    from app.services.media_storage_service import LocalMediaStorageService

    initialize_database(reset=True)
    seed_demo_users()
    seed_demo_catalog()
    seed_demo_size_charts()

    settings = get_settings()
    settings.ai_enabled = True
    settings.ai_try_on_enabled = True
    settings.ai_try_on_primary_model = "google/gemini-2.5-flash-image"
    settings.ai_try_on_fallback_model = "black-forest-labs/flux.2-flex"

    client = _MultiProductClient()
    storage = LocalMediaStorageService(tmp_path, "/media")

    with SessionLocal() as session:
        service = AITryOnJobService(
            session,
            openrouter_client=client,
            media_storage=storage,
        )
        job = service.create_job_from_bytes(
            user_id=1,
            product_id=1,
            image_bytes=PNG_BYTES,
            filename="person.png",
            content_type="image/png",
            body_measurements={"chest_cm": 94.0, "waist_cm": 76.0, "hips_cm": 102.0},
            style_product_ids=[1, 3],
        )

        worker = AITryOnWorkerService(
            session,
            openrouter_client=client,
            media_storage=storage,
        )
        processed = worker.process_job(job.id)

    assert processed is not None
    assert processed.status == "completed"
    assert processed.selected_model_name == settings.ai_try_on_primary_model
    assert client.last_model == settings.ai_try_on_primary_model
    assert len(client.last_images) == 3
    assert client.last_images[0]["source"] == "bytes"
    assert client.last_images[1]["source"] == "url"
    assert client.last_images[2]["source"] == "url"
    assert client.last_metadata["product_ids"] == [1, 3]
    assert "Silk Shell Top" in client.last_prompt
    assert "Minimal Trench" in client.last_prompt
