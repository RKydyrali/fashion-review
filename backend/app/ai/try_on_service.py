from __future__ import annotations

from pathlib import Path

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.ai.deterministic import build_ai_try_on_idempotency_key, compute_fit_class
from app.ai.prompts import TRY_ON_TEMPLATE_VERSION
from app.core.config import get_settings
from app.domain.ai_try_on_job_status import AITryOnJobStatus
from app.models.product import Product
from app.repositories.ai_call_repository import AICallRepository
from app.repositories.ai_try_on_repository import AITryOnRepository
from app.repositories.product_repository import ProductRepository
from app.repositories.size_chart_repository import SizeChartRepository
from app.schemas.ai import AITryOnJobRead
from app.schemas.sizing import BodyMeasurements
from app.services.media_storage_service import LocalMediaStorageService
from app.services.size_recommendation_service import SizeRecommendationService

ALLOWED_IMAGE_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}
JPEG_EXTENSIONS = {".jpg", ".jpeg"}


class AITryOnJobService:
    def __init__(
        self,
        session: Session,
        *,
        openrouter_client,
        media_storage: LocalMediaStorageService | None = None,
    ) -> None:
        settings = get_settings()
        self.session = session
        self.settings = settings
        self.openrouter_client = openrouter_client
        self.repository = AITryOnRepository(session)
        self.product_repository = ProductRepository(session)
        self.size_service = SizeRecommendationService(repository=SizeChartRepository(session))
        self.call_repository = AICallRepository(session)
        self.media_storage = media_storage or LocalMediaStorageService(settings.media_root, settings.media_url_prefix)

    def create_job_from_upload(
        self,
        *,
        user_id: int,
        product_id: int,
        style_product_ids: list[int] | None = None,
        upload: UploadFile,
        body_measurements: dict | None = None,
        product_measurements: dict | None = None,
        preferred_fit: str | None = None,
        chart_id: int | None = None,
    ) -> AITryOnJobRead:
        image_bytes = upload.file.read()
        return self.create_job_from_bytes(
            user_id=user_id,
            product_id=product_id,
            style_product_ids=style_product_ids,
            image_bytes=image_bytes,
            filename=upload.filename or "upload",
            content_type=upload.content_type or "",
            body_measurements=body_measurements,
            product_measurements=product_measurements,
            preferred_fit=preferred_fit,
            chart_id=chart_id,
        )

    def create_job_from_bytes(
        self,
        *,
        user_id: int,
        product_id: int,
        style_product_ids: list[int] | None = None,
        image_bytes: bytes,
        filename: str,
        content_type: str,
        body_measurements: dict | None = None,
        product_measurements: dict | None = None,
        preferred_fit: str | None = None,
        chart_id: int | None = None,
    ) -> AITryOnJobRead:
        if not self.settings.ai_enabled or not self.settings.ai_try_on_enabled:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="AI try-on is disabled")
        requested_product_ids = style_product_ids or [product_id]
        products = self._validate_products(requested_product_ids)
        product = products[0]
        extension = self._validate_upload(filename=filename, content_type=content_type, image_bytes=image_bytes)
        body = BodyMeasurements.model_validate(body_measurements) if body_measurements else None
        fit = compute_fit_class(
            normalized_category=product.normalized_category,
            body_measurements=body,
            product_measurements=product_measurements,
            preferred_fit=preferred_fit,
            chart_id=chart_id,
            size_service=self.size_service,
        )
        idempotency_key = build_ai_try_on_idempotency_key(
            image_bytes,
            requested_product_ids,
            fit.fit_class.value,
            primary_model_name=self.settings.ai_try_on_primary_model,
            prompt_template_version=TRY_ON_TEMPLATE_VERSION,
        )
        reusable = self.repository.find_reusable(user_id=user_id, idempotency_key=idempotency_key)
        if reusable is not None:
            return self._to_read(reusable)

        source_asset = self.repository.create_asset(
            user_id=user_id,
            asset_kind="try_on_source",
            storage_path="pending",
            content_type=content_type,
            metadata_json={"filename": filename},
        )
        source_asset.storage_path = self._source_asset_path(source_asset.id, extension)
        self.media_storage.save_bytes(source_asset.storage_path, image_bytes)

        job = self.repository.create_job(
            user_id=user_id,
            product_id=product_id,
            source_asset_id=source_asset.id,
            result_asset_id=None,
            idempotency_key=idempotency_key,
            fit_class=fit.fit_class,
            fit_reason=fit.fit_reason,
            provider_name="openrouter",
            primary_model_name=self.settings.ai_try_on_primary_model,
            fallback_model_name=self.settings.ai_try_on_fallback_model,
            selected_model_name=None,
            prompt_template_version=TRY_ON_TEMPLATE_VERSION,
            status=AITryOnJobStatus.QUEUED,
            attempt_count=0,
            max_attempts=self.settings.ai_try_on_max_attempts,
            request_snapshot={
                "product_id": product_id,
                "product_ids": requested_product_ids,
                "body_measurements": body.model_dump(mode="json") if body is not None else None,
                "product_measurements": product_measurements,
                "preferred_fit": preferred_fit,
                "chart_id": chart_id,
            },
            deterministic_snapshot=fit.deterministic_snapshot,
            last_ai_call_id=None,
            error_message=None,
        )
        self.repository.create_event(job_id=job.id, status=job.status.value, message="job queued", error_metadata=None)
        self.session.commit()
        return self._to_read(job)

    def get_job(self, *, user_id: int, job_id: int) -> AITryOnJobRead:
        job = self.repository.get_job(job_id)
        if job is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="AI try-on job not found")
        if job.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
        return self._to_read(job)

    def _validate_products(self, product_ids: list[int]) -> list[Product]:
        if not 1 <= len(product_ids) <= 3:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Select between 1 and 3 products")

        products = self.product_repository.list_by_ids(product_ids)
        if len(products) != len(product_ids):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown product selection")

        products_by_id = {product.id: product for product in products}
        ordered_products = [products_by_id[product_id] for product_id in product_ids]
        for product in ordered_products:
            if not product.is_active or not product.is_available or not product.reference_image_url:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Selected product is not available for try-on")
        return ordered_products

    def _validate_upload(self, *, filename: str, content_type: str, image_bytes: bytes) -> str:
        if content_type not in ALLOWED_IMAGE_TYPES:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported image format")
        if len(image_bytes) > self.settings.try_on_max_upload_bytes:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded image exceeds size limit")
        extension = Path(filename).suffix.casefold()
        if extension:
            expected_extension = ALLOWED_IMAGE_TYPES[content_type]
            if not (extension == expected_extension or (content_type == "image/jpeg" and extension in JPEG_EXTENSIONS)):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Image extension does not match content type")
        else:
            extension = ALLOWED_IMAGE_TYPES[content_type]
        return ".jpg" if extension in JPEG_EXTENSIONS else extension

    def _source_asset_path(self, asset_id: int, extension: str) -> str:
        return f"ai_try_on/assets/{asset_id}/source{extension}"

    def result_asset_path(self, asset_id: int, extension: str) -> str:
        return f"ai_try_on/assets/{asset_id}/result{extension}"

    def _to_read(self, job) -> AITryOnJobRead:
        source_asset = self.repository.get_asset(job.source_asset_id)
        result_asset = self.repository.get_asset(job.result_asset_id)
        return AITryOnJobRead(
            id=job.id,
            status=job.status.value,
            product_id=job.product_id,
            fit_class=job.fit_class.value,
            fit_reason=job.fit_reason,
            source_image_url=self.media_storage.url_for(source_asset.storage_path if source_asset else None) or "",
            result_image_url=self.media_storage.url_for(result_asset.storage_path if result_asset else None),
            ai_status="completed" if job.status.value == "completed" else "fallback",
            provider_name=job.provider_name,
            model_name=job.selected_model_name,
            prompt_template_version=job.prompt_template_version,
            used_fallback=job.selected_model_name == job.fallback_model_name and job.selected_model_name is not None,
            primary_model_name=job.primary_model_name,
            fallback_model_name=job.fallback_model_name,
            selected_model_name=job.selected_model_name,
            error_message=job.error_message,
            created_at=job.created_at,
            updated_at=job.updated_at,
        )
