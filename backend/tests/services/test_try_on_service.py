from pathlib import Path


PNG_BYTES = b"\x89PNG\r\n\x1a\n" + (b"0" * 64)


class _SlowProvider:
    def __init__(self) -> None:
        self.calls = 0

    def generate(self, *, source_image_bytes: bytes, source_content_type: str, garment_image_urls: list[str]) -> tuple[bytes, str]:
        import time

        self.calls += 1
        time.sleep(0.05)
        return (source_image_bytes, "image/png")


class _SuccessfulProvider:
    def __init__(self) -> None:
        self.calls = 0
        self.last_urls: list[str] = []

    def generate(self, *, source_image_bytes: bytes, source_content_type: str, garment_image_urls: list[str]) -> tuple[bytes, str]:
        self.calls += 1
        self.last_urls = garment_image_urls
        return (b"rendered-image", "image/png")


def test_try_on_service_generates_stable_idempotency_key_and_storage_paths(tmp_path: Path) -> None:
    from app.services.media_storage_service import LocalMediaStorageService
    from app.services.try_on_service import build_try_on_idempotency_key

    key_one = build_try_on_idempotency_key(PNG_BYTES, [2, 1])
    key_two = build_try_on_idempotency_key(PNG_BYTES, [2, 1])
    key_three = build_try_on_idempotency_key(PNG_BYTES, [1, 2])
    storage = LocalMediaStorageService(tmp_path, "/media")

    assert key_one == key_two
    assert key_one != key_three
    assert storage.source_relative_path(7, ".png") == "try_on/7/source/original.png"
    assert storage.render_relative_path(7, ".png") == "try_on/7/render/result.png"


def test_try_on_worker_requeues_timeout_until_retry_cap_then_fails(tmp_path: Path) -> None:
    from app.core.database import SessionLocal, initialize_database, seed_demo_catalog, seed_demo_users
    from app.domain.try_on_status import TryOnStatus
    from app.services.media_storage_service import LocalMediaStorageService
    from app.services.try_on_service import TryOnService
    from app.services.try_on_worker_service import TryOnWorkerService

    initialize_database(reset=True)
    seed_demo_users()
    seed_demo_catalog()

    storage = LocalMediaStorageService(tmp_path, "/media")

    with SessionLocal() as session:
        create_service = TryOnService(session, media_storage=storage)
        created = create_service.create_session_from_bytes(
            user_id=1,
            product_ids=[1],
            image_bytes=PNG_BYTES,
            filename="person.png",
            content_type="image/png",
        )

        worker = TryOnWorkerService(
            session,
            media_storage=storage,
            provider=_SlowProvider(),
            provider_timeout_seconds=0.01,
            max_attempts=3,
        )

        first = worker.process_next_session()
        second = worker.process_next_session()
        third = worker.process_next_session()
        refreshed = worker.repository.get_by_id(created.id)

    assert first is not None
    assert second is not None
    assert third is not None
    assert refreshed is not None
    assert refreshed.status == TryOnStatus.FAILED
    assert refreshed.attempt_count == 3
    assert "timeout" in (refreshed.error_message or "").lower()


def test_try_on_worker_completes_and_preserves_product_order_for_provider(tmp_path: Path) -> None:
    from app.core.database import SessionLocal, initialize_database, seed_demo_catalog, seed_demo_users
    from app.domain.try_on_status import TryOnStatus
    from app.services.media_storage_service import LocalMediaStorageService
    from app.services.try_on_service import TryOnService
    from app.services.try_on_worker_service import TryOnWorkerService

    initialize_database(reset=True)
    seed_demo_users()
    seed_demo_catalog()

    provider = _SuccessfulProvider()
    storage = LocalMediaStorageService(tmp_path, "/media")

    with SessionLocal() as session:
        create_service = TryOnService(session, media_storage=storage)
        created = create_service.create_session_from_bytes(
            user_id=1,
            product_ids=[2, 1],
            image_bytes=PNG_BYTES,
            filename="person.png",
            content_type="image/png",
        )

        worker = TryOnWorkerService(
            session,
            media_storage=storage,
            provider=provider,
            provider_timeout_seconds=1.0,
            max_attempts=3,
        )
        processed = worker.process_next_session()

    assert processed is not None
    assert processed.status == TryOnStatus.COMPLETED
    assert processed.rendered_image_url.endswith("/media/try_on/1/render/result.png")
    assert provider.last_urls == [
        "https://example.test/assets/products/bot-001.png",
        "https://example.test/assets/products/top-001.png",
    ]
