from __future__ import annotations

from dataclasses import dataclass, field
from threading import Lock

from fastapi import WebSocket

from app.domain.roles import UserRole
from app.websocket.events import RealtimeEvent

USER_CHANNEL_PREFIX = "user:"
BRANCH_CHANNEL_PREFIX = "branch:"
PRODUCTION_CHANNEL = "role:production"


@dataclass(slots=True)
class ConnectionRecord:
    websocket: WebSocket
    user_id: int
    role: UserRole
    branch_id: int | None
    subscriptions: set[str] = field(default_factory=set)


class ConnectionManager:
    def __init__(self) -> None:
        self._connections: dict[int, ConnectionRecord] = {}
        self._lock = Lock()

    async def connect(
        self,
        websocket: WebSocket,
        *,
        user_id: int,
        role: UserRole,
        branch_id: int | None = None,
    ) -> ConnectionRecord:
        subscriptions = self.default_channels_for(user_id=user_id, role=role, branch_id=branch_id)
        record = ConnectionRecord(
            websocket=websocket,
            user_id=user_id,
            role=role,
            branch_id=branch_id,
            subscriptions=subscriptions,
        )
        await websocket.accept()
        with self._lock:
            self._connections[id(websocket)] = record
        return record

    async def disconnect(self, websocket: WebSocket) -> None:
        with self._lock:
            self._connections.pop(id(websocket), None)

    async def subscribe(self, websocket: WebSocket, channel: str) -> bool:
        with self._lock:
            record = self._connections.get(id(websocket))
            if record is None or not self.is_channel_allowed(record, channel):
                return False
            record.subscriptions.add(channel)
            return True

    async def unsubscribe(self, websocket: WebSocket, channel: str) -> bool:
        with self._lock:
            record = self._connections.get(id(websocket))
            if record is None or not self.is_channel_allowed(record, channel):
                return False
            record.subscriptions.discard(channel)
            return True

    async def publish_event(self, event: RealtimeEvent) -> None:
        with self._lock:
            targets = [
                record
                for record in self._connections.values()
                if record.subscriptions.intersection(event.channels)
            ]

        stale_connections: list[WebSocket] = []
        payload = event.model_dump(mode="json")
        for record in targets:
            try:
                await record.websocket.send_json(payload)
            except Exception:
                stale_connections.append(record.websocket)

        for websocket in stale_connections:
            await self.disconnect(websocket)

    def default_channels_for(self, *, user_id: int, role: UserRole, branch_id: int | None) -> set[str]:
        subscriptions = {f"{USER_CHANNEL_PREFIX}{user_id}"}
        if role == UserRole.FRANCHISEE and branch_id is not None:
            subscriptions.add(f"{BRANCH_CHANNEL_PREFIX}{branch_id}")
        if role == UserRole.PRODUCTION:
            subscriptions.add(PRODUCTION_CHANNEL)
        return subscriptions

    def is_channel_allowed(self, record: ConnectionRecord, channel: str) -> bool:
        if channel == f"{USER_CHANNEL_PREFIX}{record.user_id}":
            return True
        if record.role == UserRole.FRANCHISEE and record.branch_id is not None:
            return channel == f"{BRANCH_CHANNEL_PREFIX}{record.branch_id}"
        if record.role == UserRole.PRODUCTION:
            return channel == PRODUCTION_CHANNEL
        return False


manager = ConnectionManager()
