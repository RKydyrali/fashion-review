from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.ai_try_on_job_status import AITryOnJobStatus
from app.models.ai_asset import AIAsset
from app.models.ai_try_on_event import AITryOnEvent
from app.models.ai_try_on_job import AITryOnJob


class AITryOnRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_asset(self, **values) -> AIAsset:
        asset = AIAsset(**values)
        self.session.add(asset)
        self.session.flush()
        return asset

    def create_job(self, **values) -> AITryOnJob:
        job = AITryOnJob(**values)
        self.session.add(job)
        self.session.flush()
        return job

    def create_event(self, **values) -> AITryOnEvent:
        event = AITryOnEvent(**values)
        self.session.add(event)
        self.session.flush()
        return event

    def get_job(self, job_id: int) -> AITryOnJob | None:
        return self.session.get(AITryOnJob, job_id)

    def get_asset(self, asset_id: int | None) -> AIAsset | None:
        if asset_id is None:
            return None
        return self.session.get(AIAsset, asset_id)

    def next_queued_job(self) -> AITryOnJob | None:
        statement = (
            select(AITryOnJob)
            .where(AITryOnJob.status == AITryOnJobStatus.QUEUED)
            .order_by(AITryOnJob.id)
            .limit(1)
        )
        return self.session.scalar(statement)

    def find_reusable(self, *, user_id: int, idempotency_key: str) -> AITryOnJob | None:
        statement = (
            select(AITryOnJob)
            .where(
                AITryOnJob.user_id == user_id,
                AITryOnJob.idempotency_key == idempotency_key,
                AITryOnJob.status.in_(
                    (
                        AITryOnJobStatus.QUEUED,
                        AITryOnJobStatus.PROCESSING,
                        AITryOnJobStatus.COMPLETED,
                    )
                ),
            )
            .order_by(AITryOnJob.id.desc())
            .limit(1)
        )
        return self.session.scalar(statement)
