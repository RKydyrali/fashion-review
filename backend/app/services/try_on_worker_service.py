from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.domain.try_on_status import TryOnStatus
from app.repositories.product_repository import ProductRepository
from app.repositories.try_on_repository import TryOnRepository
from app.schemas.try_on import TryOnSessionRead
from app.services.media_storage_service import LocalMediaStorageService
from app.services.try_on_provider import FluxTryOnProvider, ProviderTimeoutError, TryOnProvider, TryOnProviderResult
from app.services.try_on_service import ALLOWED_IMAGE_TYPES, TryOnService
from app.websocket.try_on_publisher import (
    TryOnEventPublisher,
    realtime_try_on_event_publisher,
)


class TryOnWorkerService:
    def __init__(
        self,
        session: Session,
        *,
        media_storage: LocalMediaStorageService | None = None,
        provider: TryOnProvider | None = None,
        event_publisher: TryOnEventPublisher | None = None,
        provider_timeout_seconds: float | None = None,
        max_attempts: int | None = None,
    ) -> None:
        settings = get_settings()
        self.session = session
        self.repository = TryOnRepository(session)
        self.products = ProductRepository(session)
        self.media_storage = media_storage or LocalMediaStorageService(settings.media_root, settings.media_url_prefix)
        self.provider = provider or FluxTryOnProvider(api_url=settings.flux_api_url)
        self.event_publisher = event_publisher or realtime_try_on_event_publisher
        self.provider_timeout_seconds = provider_timeout_seconds or settings.try_on_provider_timeout_seconds
        self.max_attempts = max_attempts or settings.try_on_max_attempts
        self.read_service = TryOnService(
            session,
            media_storage=self.media_storage,
            event_publisher=self.event_publisher,
            max_attempts=self.max_attempts,
        )

    def process_next_session(self) -> TryOnSessionRead | None:
        session_model = self.repository.next_queued()
        if session_model is None:
            return None

        session_model.status = TryOnStatus.PROCESSING
        session_model.attempt_count += 1
        self.repository.save(session_model)
        self.session.commit()
        self.event_publisher.publish_processing(self.read_service._to_read(session_model), user_id=session_model.user_id)

        start_time = time.monotonic()
        try:
            source_image_bytes = self.media_storage.read_bytes(session_model.source_image_path)
            products = self.products.list_by_ids(list(session_model.product_ids))
            garment_image_urls = [product.reference_image_url for product in products if product.reference_image_url]
            result = self._call_provider(
                source_image_bytes=source_image_bytes,
                source_content_type=self._content_type_for_path(session_model.source_image_path),
                garment_image_urls=garment_image_urls,
            )

            render_extension = ALLOWED_IMAGE_TYPES.get(result.content_type, ".png")
            session_model.rendered_image_path = self.media_storage.render_relative_path(session_model.id, render_extension)
            self.media_storage.save_bytes(session_model.rendered_image_path, result.image_bytes)
            session_model.provider_latency_ms = int((time.monotonic() - start_time) * 1000)
            session_model.status = TryOnStatus.COMPLETED
            session_model.error_message = None
            self.repository.save(session_model)
            self.session.commit()
            session_read = self.read_service._to_read(session_model)
            self.event_publisher.publish_completed(session_read, user_id=session_model.user_id)
            return session_read
        except Exception as exc:
            session_model.provider_latency_ms = int((time.monotonic() - start_time) * 1000)
            session_model.error_message = str(exc)
            if session_model.attempt_count >= self.max_attempts:
                session_model.status = TryOnStatus.FAILED
            else:
                session_model.status = TryOnStatus.QUEUED
            self.repository.save(session_model)
            self.session.commit()
            session_read = self.read_service._to_read(session_model)
            if session_model.status == TryOnStatus.FAILED:
                self.event_publisher.publish_failed(session_read, user_id=session_model.user_id)
            return session_read

    def _call_provider(
        self,
        *,
        source_image_bytes: bytes,
        source_content_type: str,
        garment_image_urls: list[str],
    ) -> TryOnProviderResult:
        executor = ThreadPoolExecutor(max_workers=1)
        future = executor.submit(
            self.provider.generate,
            source_image_bytes=source_image_bytes,
            source_content_type=source_content_type,
            garment_image_urls=garment_image_urls,
        )
        try:
            result = future.result(timeout=self.provider_timeout_seconds)
        except FutureTimeoutError as exc:
            raise ProviderTimeoutError("Try-on provider timeout") from exc
        finally:
            executor.shutdown(wait=False, cancel_futures=True)

        if isinstance(result, TryOnProviderResult):
            return result
        image_bytes, content_type = result
        return TryOnProviderResult(image_bytes=image_bytes, content_type=content_type)

    def _content_type_for_path(self, relative_path: str) -> str:
        extension = Path(relative_path).suffix.casefold()
        if extension in {".jpg", ".jpeg"}:
            return "image/jpeg"
        if extension == ".webp":
            return "image/webp"
        return "image/png"
