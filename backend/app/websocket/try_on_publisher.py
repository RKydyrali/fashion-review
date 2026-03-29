from __future__ import annotations

import asyncio
from typing import Protocol

from anyio import from_thread

from app.schemas.try_on import TryOnRealtimePayload, TryOnSessionRead
from app.websocket.connection_manager import USER_CHANNEL_PREFIX, manager
from app.websocket.events import RealtimeEvent


class TryOnEventPublisher(Protocol):
    def publish_queued(self, session: TryOnSessionRead, *, user_id: int) -> None: ...

    def publish_processing(self, session: TryOnSessionRead, *, user_id: int) -> None: ...

    def publish_completed(self, session: TryOnSessionRead, *, user_id: int) -> None: ...

    def publish_failed(self, session: TryOnSessionRead, *, user_id: int) -> None: ...


class NullTryOnEventPublisher:
    def publish_queued(self, session: TryOnSessionRead, *, user_id: int) -> None:
        return None

    def publish_processing(self, session: TryOnSessionRead, *, user_id: int) -> None:
        return None

    def publish_completed(self, session: TryOnSessionRead, *, user_id: int) -> None:
        return None

    def publish_failed(self, session: TryOnSessionRead, *, user_id: int) -> None:
        return None


class WebSocketTryOnEventPublisher:
    def publish_queued(self, session: TryOnSessionRead, *, user_id: int) -> None:
        self._publish(self._event("try_on_queued", session, user_id=user_id))

    def publish_processing(self, session: TryOnSessionRead, *, user_id: int) -> None:
        self._publish(self._event("try_on_processing", session, user_id=user_id))

    def publish_completed(self, session: TryOnSessionRead, *, user_id: int) -> None:
        self._publish(self._event("try_on_completed", session, user_id=user_id))

    def publish_failed(self, session: TryOnSessionRead, *, user_id: int) -> None:
        self._publish(self._event("try_on_failed", session, user_id=user_id))

    def _event(self, name: str, session: TryOnSessionRead, *, user_id: int) -> RealtimeEvent:
        payload = TryOnRealtimePayload(
            session_id=session.id,
            user_id=user_id,
            status=session.status,
            rendered_image_url=session.rendered_image_url,
            error_message=session.error_message,
        )
        return RealtimeEvent(
            event=name,
            channels=[f"{USER_CHANNEL_PREFIX}{user_id}"],
            payload=payload.model_dump(mode="json"),
        )

    def _publish(self, event: RealtimeEvent) -> None:
        try:
            from_thread.run(manager.publish_event, event)
        except RuntimeError:
            asyncio.run(manager.publish_event(event))


realtime_try_on_event_publisher = WebSocketTryOnEventPublisher()
