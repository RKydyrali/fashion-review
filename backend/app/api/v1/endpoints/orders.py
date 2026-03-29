from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import CurrentUser, get_order_service, require_roles
from app.domain.roles import UserRole
from app.schemas.order import OrderCancelRequest, OrderCreate, OrderRead, OrderStatusUpdate, UserContext
from app.domain.order_status import OrderStatus
from app.services.order_service import OrderService

router = APIRouter(prefix="/orders", tags=["orders"])
client_router = APIRouter(prefix="/client", tags=["client"])
ClientUser = Annotated[CurrentUser, Depends(require_roles(UserRole.CLIENT))]


@client_router.get("/orders", response_model=list[OrderRead])
def list_client_orders(
    current_user: ClientUser,
    service: Annotated[OrderService, Depends(get_order_service)],
) -> list[OrderRead]:
    return service.list_client_orders(
        UserContext(id=current_user.id, role=current_user.role),
    )


@client_router.post("/orders", response_model=OrderRead, status_code=201)
def create_client_order(
    payload: OrderCreate,
    current_user: ClientUser,
    service: Annotated[OrderService, Depends(get_order_service)],
) -> OrderRead:
    return service.create_order(
        UserContext(id=current_user.id, role=current_user.role),
        payload,
    )


@router.patch("/{order_id}/status", response_model=OrderRead)
def update_order_status(
    order_id: int,
    payload: OrderStatusUpdate,
    current_user: CurrentUser,
    service: Annotated[OrderService, Depends(get_order_service)],
) -> OrderRead:
    return service.update_order_status(
        order_id,
        payload,
        UserContext(id=current_user.id, role=current_user.role),
    )


@router.post("/{order_id}/cancel", response_model=OrderRead)
def cancel_order(
    order_id: int,
    payload: OrderCancelRequest,
    current_user: CurrentUser,
    service: Annotated[OrderService, Depends(get_order_service)],
) -> OrderRead:
    return service.cancel_order(
        order_id,
        payload,
        UserContext(id=current_user.id, role=current_user.role),
    )


@client_router.post("/orders/{order_id}/pickup", response_model=OrderRead)
def pickup_order(
    order_id: int,
    current_user: ClientUser,
    service: Annotated[OrderService, Depends(get_order_service)],
) -> OrderRead:
    return service.update_order_status(
        order_id,
        OrderStatusUpdate(status="picked_up"),
        UserContext(id=current_user.id, role=current_user.role),
    )
