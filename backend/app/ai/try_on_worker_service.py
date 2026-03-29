from __future__ import annotations

from app.ai.client import OpenRouterError, OpenRouterImageResult
from app.ai.prompts import TRY_ON_TEMPLATE_VERSION, try_on_prompt
from app.ai.try_on_service import AITryOnJobService
from app.core.config import get_settings
from app.domain.ai_try_on_job_status import AITryOnJobStatus
from app.repositories.ai_call_repository import AICallRepository
from app.repositories.ai_try_on_repository import AITryOnRepository
from app.repositories.product_repository import ProductRepository
from app.services.media_storage_service import LocalMediaStorageService


class AITryOnWorkerService:
    def __init__(
        self,
        session,
        *,
        openrouter_client,
        media_storage: LocalMediaStorageService | None = None,
    ) -> None:
        self.session = session
        self.settings = get_settings()
        self.openrouter_client = openrouter_client
        self.repository = AITryOnRepository(session)
        self.products = ProductRepository(session)
        self.calls = AICallRepository(session)
        self.media_storage = media_storage or LocalMediaStorageService(self.settings.media_root, self.settings.media_url_prefix)
        self.read_service = AITryOnJobService(session, openrouter_client=openrouter_client, media_storage=self.media_storage)

    def process_next_job(self):
        job = self.repository.next_queued_job()
        if job is None:
            return None
        return self._process_job(job)

    def process_job(self, job_id: int):
        job = self.repository.get_job(job_id)
        if job is None:
            return None
        if job.status != AITryOnJobStatus.QUEUED:
            return self.read_service.get_job(user_id=job.user_id, job_id=job.id)
        return self._process_job(job)

    def _process_job(self, job):
        request_snapshot = job.request_snapshot or {}
        selected_product_ids = request_snapshot.get("product_ids") or [job.product_id]
        products = self.products.list_by_ids(selected_product_ids)
        products_by_id = {product.id: product for product in products}
        ordered_products = [products_by_id[product_id] for product_id in selected_product_ids if product_id in products_by_id]
        product = ordered_products[0]
        source_asset = self.repository.get_asset(job.source_asset_id)
        if source_asset is None:
            job.status = AITryOnJobStatus.FAILED
            job.error_message = "Missing source asset"
            self.repository.create_event(job_id=job.id, status=job.status.value, message=job.error_message, error_metadata=None)
            self.session.commit()
            return self.read_service.get_job(user_id=job.user_id, job_id=job.id)

        job.status = AITryOnJobStatus.PROCESSING
        job.attempt_count += 1
        self.repository.create_event(job_id=job.id, status=job.status.value, message="job processing", error_metadata=None)
        self.session.commit()

        prompt = try_on_prompt(
            language="en",
            garments=[
                {"name": product.name, "category": product.normalized_category}
                for product in ordered_products
            ],
            fit_class=job.fit_class.value,
        )
        image_inputs = [
            {
                "source": "bytes",
                "bytes": self.media_storage.read_bytes(source_asset.storage_path),
                "content_type": source_asset.content_type,
            }
        ]
        for product in ordered_products:
            reference_relative_path = self.media_storage.relative_path_from_url(product.reference_image_url)
            if reference_relative_path is not None:
                image_inputs.append(
                    {
                        "source": "bytes",
                        "bytes": self.media_storage.read_bytes(reference_relative_path),
                        "content_type": self._content_type_for_path(reference_relative_path),
                    }
                )
            else:
                image_inputs.append(
                    {
                        "source": "url",
                        "url": product.reference_image_url,
                    }
                )
        try:
            result = self._generate_with_model(job=job, model_name=job.primary_model_name, prompt=prompt, images=image_inputs)
        except OpenRouterError as primary_error:
            self.repository.create_event(
                job_id=job.id,
                status=job.status.value,
                message="primary model failed, retrying with fallback",
                error_metadata={"error": str(primary_error)},
            )
            try:
                result = self._generate_with_model(job=job, model_name=job.fallback_model_name, prompt=prompt, images=image_inputs)
            except OpenRouterError as fallback_error:
                job.status = AITryOnJobStatus.FAILED
                job.error_message = str(fallback_error)
                self.repository.create_event(job_id=job.id, status=job.status.value, message=job.error_message, error_metadata={"error": str(fallback_error)})
                self.session.commit()
                return self.read_service.get_job(user_id=job.user_id, job_id=job.id)

        result_asset = self.repository.create_asset(
            user_id=job.user_id,
            asset_kind="try_on_result",
            storage_path="pending",
            content_type=result.content_type,
            metadata_json={"job_id": job.id},
        )
        extension = ".png" if result.content_type == "image/png" else ".jpg"
        result_asset.storage_path = self.read_service.result_asset_path(result_asset.id, extension)
        self.media_storage.save_bytes(result_asset.storage_path, result.image_bytes)

        job.result_asset_id = result_asset.id
        job.status = AITryOnJobStatus.COMPLETED
        job.selected_model_name = result.model_name
        job.prompt_template_version = TRY_ON_TEMPLATE_VERSION
        job.error_message = None
        self.repository.create_event(job_id=job.id, status=job.status.value, message="job completed", error_metadata=None)
        self.session.commit()
        return self.read_service.get_job(user_id=job.user_id, job_id=job.id)

    def _generate_with_model(self, *, job, model_name: str, prompt: str, images: list[dict]):
        try:
            result = self.openrouter_client.generate_image(
                model=model_name,
                prompt=prompt,
                prompt_template_version=TRY_ON_TEMPLATE_VERSION,
                images=images,
                metadata={
                    "job_id": job.id,
                    "fit_class": job.fit_class.value,
                    "product_ids": (job.request_snapshot or {}).get("product_ids") or [job.product_id],
                },
            )
            if isinstance(result, dict):
                result = OpenRouterImageResult(
                    provider_name=result["provider_name"],
                    model_name=result["model_name"],
                    prompt_template_version=result["prompt_template_version"],
                    latency_ms=result["latency_ms"],
                    image_bytes=result["image_bytes"],
                    content_type=result["content_type"],
                    raw_response=result["raw_response"],
                )
            provider_name = result.provider_name
            returned_model_name = result.model_name
            prompt_template_version = result.prompt_template_version
            latency_ms = result.latency_ms
            raw_response = result.raw_response
            call = self.calls.create(
                user_id=job.user_id,
                feature_name="ai_try_on",
                provider_name=provider_name,
                model_name=returned_model_name,
                prompt_template_version=prompt_template_version,
                status="completed",
                latency_ms=latency_ms,
                request_payload={"job_id": job.id, "fit_class": job.fit_class.value},
                response_payload=raw_response,
                error_metadata=None,
                error_message=None,
                related_resource_type="ai_try_on_job",
                related_resource_id=job.id,
            )
            job.last_ai_call_id = call.id
            self.session.flush()
            return result
        except Exception as exc:
            call = self.calls.create(
                user_id=job.user_id,
                feature_name="ai_try_on",
                provider_name="openrouter",
                model_name=model_name,
                prompt_template_version=TRY_ON_TEMPLATE_VERSION,
                status="failed",
                latency_ms=None,
                request_payload={"job_id": job.id, "fit_class": job.fit_class.value},
                response_payload=None,
                error_metadata={"exception": exc.__class__.__name__},
                error_message=str(exc),
                related_resource_type="ai_try_on_job",
                related_resource_id=job.id,
            )
            job.last_ai_call_id = call.id
            self.session.flush()
            raise OpenRouterError(str(exc)) from exc

    def _content_type_for_path(self, relative_path: str) -> str:
        extension = self.media_storage.root.joinpath(relative_path).suffix.casefold()
        if extension in {".jpg", ".jpeg"}:
            return "image/jpeg"
        if extension == ".webp":
            return "image/webp"
        return "image/png"
