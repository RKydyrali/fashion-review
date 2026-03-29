from __future__ import annotations

from hashlib import sha256
from pathlib import Path

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.domain.try_on_status import TryOnStatus
from app.models.try_on_session import TryOnSession
from app.repositories.product_repository import ProductRepository
from app.repositories.try_on_repository import TryOnRepository
from app.schemas.try_on import TryOnSessionRead
from app.services.media_storage_service import LocalMediaStorageService
from app.websocket.try_on_publisher import NullTryOnEventPublisher, TryOnEventPublisher

ALLOWED_IMAGE_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}
JPEG_EXTENSIONS = {".jpg", ".jpeg"}


def build_try_on_idempotency_key(image_bytes: bytes, product_ids: list[int]) -> str:
    payload = image_bytes + b"|" + ",".join(str(product_id) for product_id in product_ids).encode("utf-8")
    return sha256(payload).hexdigest()


class TryOnService:
    def __init__(
        self,
        session: Session,
        *,
        media_storage: LocalMediaStorageService | None = None,
        event_publisher: TryOnEventPublisher | None = None,
        max_upload_bytes: int | None = None,
        max_attempts: int | None = None,
    ) -> None:
        settings = get_settings()
        self.session = session
        self.products = ProductRepository(session)
        self.repository = TryOnRepository(session)
        self.media_storage = media_storage or LocalMediaStorageService(settings.media_root, settings.media_url_prefix)
        self.event_publisher = event_publisher or NullTryOnEventPublisher()
        self.max_upload_bytes = max_upload_bytes or settings.try_on_max_upload_bytes
        self.max_attempts = max_attempts or settings.try_on_max_attempts

    def create_or_reuse_session_from_upload(
        self,
        *,
        user_id: int,
        product_ids: list[int],
        upload: UploadFile,
    ) -> tuple[TryOnSessionRead, bool]:
        content_type = upload.content_type or ""
        image_bytes = upload.file.read()
        return self.create_or_reuse_session_from_bytes(
            user_id=user_id,
            product_ids=product_ids,
            image_bytes=image_bytes,
            filename=upload.filename or "upload",
            content_type=content_type,
        )

    def create_session_from_bytes(
        self,
        *,
        user_id: int,
        product_ids: list[int],
        image_bytes: bytes,
        filename: str,
        content_type: str,
    ) -> TryOnSessionRead:
        session_read, _ = self.create_or_reuse_session_from_bytes(
            user_id=user_id,
            product_ids=product_ids,
            image_bytes=image_bytes,
            filename=filename,
            content_type=content_type,
        )
        return session_read

    def create_or_reuse_session_from_bytes(
        self,
        *,
        user_id: int,
        product_ids: list[int],
        image_bytes: bytes,
        filename: str,
        content_type: str,
    ) -> tuple[TryOnSessionRead, bool]:
        validated_product_ids = self._validate_product_ids(product_ids)
        extension = self._validate_upload(filename=filename, content_type=content_type, image_bytes=image_bytes)
        idempotency_key = build_try_on_idempotency_key(image_bytes, validated_product_ids)

        existing = self.repository.find_reusable_by_idempotency(
            user_id=user_id,
            idempotency_key=idempotency_key,
        )
        if existing is not None:
            return self._to_read(existing), False

        session_model = TryOnSession(
            user_id=user_id,
            product_ids=validated_product_ids,
            idempotency_key=idempotency_key,
            source_image_path="pending",
            rendered_image_path=None,
            provider_name="flux",
            status=TryOnStatus.QUEUED,
            attempt_count=0,
            max_attempts=self.max_attempts,
            error_message=None,
        )
        self.repository.save(session_model)
        session_model.source_image_path = self.media_storage.source_relative_path(session_model.id, extension)
        self.media_storage.save_bytes(session_model.source_image_path, image_bytes)
        self.session.commit()

        session_read = self._to_read(session_model)
        self.event_publisher.publish_queued(session_read, user_id=user_id)
        return session_read, True

    def get_session(self, *, user_id: int, session_id: int) -> TryOnSessionRead:
        session_model = self.repository.get_by_id(session_id)
        if session_model is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Try-on session not found")
        if session_model.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
        return self._to_read(session_model)

    def _validate_product_ids(self, product_ids: list[int]) -> list[int]:
        if not 1 <= len(product_ids) <= 3:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Select between 1 and 3 products")

        products = self.products.list_by_ids(product_ids)
        if len(products) != len(product_ids):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown product selection")

        for product in products:
            if not product.is_active or not product.is_available:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Selected product is not available")
            if not product.reference_image_url:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Selected product has no try-on reference image")
        return product_ids

    def _validate_upload(self, *, filename: str, content_type: str, image_bytes: bytes) -> str:
        if content_type not in ALLOWED_IMAGE_TYPES:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported image format")
        if len(image_bytes) > self.max_upload_bytes:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded image exceeds size limit")

        extension = Path(filename).suffix.casefold()
        if extension:
            expected_extension = ALLOWED_IMAGE_TYPES[content_type]
            if not (
                extension == expected_extension
                or (content_type == "image/jpeg" and extension in JPEG_EXTENSIONS)
            ):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Image extension does not match content type")
        else:
            extension = ALLOWED_IMAGE_TYPES[content_type]
        return ".jpg" if extension in JPEG_EXTENSIONS else extension

    def _to_read(self, session_model: TryOnSession) -> TryOnSessionRead:
        return TryOnSessionRead(
            id=session_model.id,
            status=session_model.status,
            source_image_url=self.media_storage.url_for(session_model.source_image_path) or "",
            rendered_image_url=self.media_storage.url_for(session_model.rendered_image_path),
            product_ids=list(session_model.product_ids),
            attempt_count=session_model.attempt_count,
            error_message=session_model.error_message,
            created_at=session_model.created_at,
            updated_at=session_model.updated_at,
        )
