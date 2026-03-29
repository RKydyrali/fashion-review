from typing import Any

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, status
from pydantic import ValidationError
from sqlalchemy import select

from app.core.database import SessionLocal
from app.domain.roles import UserRole
from app.models.branch import Branch
from app.services.auth_service import AuthService
from app.websocket.connection_manager import manager
from app.websocket.events import ChannelCommandPayload, ErrorPayload, RealtimeEvent, SubscriptionCommand

router = APIRouter()


@router.websocket("/updates")
async def websocket_updates(websocket: WebSocket) -> None:
    authenticated_user = _authenticate_websocket(websocket)
    if authenticated_user is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    branch_id = _resolve_branch_id_for_user(
        user_id=authenticated_user.id,
        role=authenticated_user.role,
    )

    await manager.connect(
        websocket,
        user_id=authenticated_user.id,
        role=authenticated_user.role,
        branch_id=branch_id,
    )

    try:
        while True:
            message = await websocket.receive_json()
            await _handle_command(websocket, message)
    except WebSocketDisconnect:
        await manager.disconnect(websocket)


def _authenticate_websocket(websocket: WebSocket):
    token = websocket.query_params.get("token")
    if not token:
        return None

    with SessionLocal() as session:
        auth_service = AuthService(session)
        try:
            user = auth_service.get_current_user(token)
        except (HTTPException, ValueError):
            return None

    if not user.is_active:
        return None
    return user


def _resolve_branch_id_for_user(*, user_id: int, role: UserRole) -> int | None:
    if role != UserRole.FRANCHISEE:
        return None

    with SessionLocal() as session:
        statement = select(Branch.id).where(Branch.manager_user_id == user_id).limit(1)
        return session.scalar(statement)


async def _handle_command(websocket: WebSocket, message: Any) -> None:
    try:
        command = SubscriptionCommand.model_validate(message)
    except ValidationError:
        await _send_event(
            websocket,
            RealtimeEvent(
                event="error",
                payload=ErrorPayload(message="Invalid websocket command").model_dump(mode="json"),
            ),
        )
        return

    if command.command == "subscribe":
        subscribed = await manager.subscribe(websocket, command.channel)
        if subscribed:
            await _send_event(
                websocket,
                RealtimeEvent(
                    event="subscribed",
                    channels=[command.channel],
                    payload=ChannelCommandPayload(channel=command.channel).model_dump(mode="json"),
                ),
            )
            return

        await _send_event(
            websocket,
            RealtimeEvent(
                event="error",
                payload=ErrorPayload(
                    message="Channel subscription is not allowed",
                    channel=command.channel,
                ).model_dump(mode="json"),
            ),
        )
        return

    unsubscribed = await manager.unsubscribe(websocket, command.channel)
    if unsubscribed:
        await _send_event(
            websocket,
            RealtimeEvent(
                event="unsubscribed",
                channels=[command.channel],
                payload=ChannelCommandPayload(channel=command.channel).model_dump(mode="json"),
            ),
        )
        return

    await _send_event(
        websocket,
        RealtimeEvent(
            event="error",
            payload=ErrorPayload(
                message="Channel unsubscription is not allowed",
                channel=command.channel,
            ).model_dump(mode="json"),
        ),
    )


async def _send_event(websocket: WebSocket, event: RealtimeEvent) -> None:
    await websocket.send_json(event.model_dump(mode="json"))
