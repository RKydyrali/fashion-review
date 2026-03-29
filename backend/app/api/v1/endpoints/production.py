from datetime import datetime, timedelta
from typing import Annotated, Optional
from pydantic import BaseModel

from fastapi import APIRouter, Depends, Query
from app.api.deps import CurrentUser, get_order_service, require_roles
from app.domain.roles import UserRole
from app.schemas.order import OrderRead, UserContext
from app.services.order_service import OrderService

router = APIRouter(prefix="/production", tags=["production"])
ProductionUser = Annotated[CurrentUser, Depends(require_roles(UserRole.PRODUCTION))]


class ProductionShiftStatus(BaseModel):
    is_open: bool
    shift_type: Optional[str] = None
    shift_started_at: Optional[str] = None
    shift_duration_minutes: int
    orders_started_today: int
    orders_completed_today: int
    orders_in_progress: int


class ProductionShiftReport(BaseModel):
    shift_date: str
    shift_type: str
    shift_started_at: str
    shift_ended_at: str
    duration_minutes: int
    orders_started: int
    orders_completed: int
    orders_incomplete: int


class ShiftStartRequest(BaseModel):
    shift_type: str


class OrderStatusUpdate(BaseModel):
    status: str


_shift_data = {
    "is_open": False,
    "shift_type": None,
    "shift_started_at": None,
    "orders_started_today": 0,
    "orders_completed_today": 0,
    "last_reset_date": None
}


def _reset_daily_counts():
    today = datetime.now().date()
    if _shift_data["last_reset_date"] != today:
        _shift_data["orders_started_today"] = 0
        _shift_data["orders_completed_today"] = 0
        _shift_data["last_reset_date"] = today


@router.get("/shift-status", response_model=ProductionShiftStatus)
def get_shift_status(
    current_user: ProductionUser,
) -> ProductionShiftStatus:
    _reset_daily_counts()
    
    is_open = _shift_data["is_open"]
    shift_duration = 0
    
    if is_open and _shift_data["shift_started_at"]:
        started = datetime.fromisoformat(_shift_data["shift_started_at"])
        shift_duration = int((datetime.now() - started).total_seconds() / 60)
    
    return ProductionShiftStatus(
        is_open=is_open,
        shift_type=_shift_data["shift_type"],
        shift_started_at=_shift_data["shift_started_at"],
        shift_duration_minutes=shift_duration,
        orders_started_today=_shift_data["orders_started_today"],
        orders_completed_today=_shift_data["orders_completed_today"],
        orders_in_progress=3
    )


@router.post("/shift/start", response_model=ProductionShiftStatus)
def start_shift(
    payload: ShiftStartRequest,
    current_user: ProductionUser,
) -> ProductionShiftStatus:
    _reset_daily_counts()
    
    shift_type = payload.shift_type
    if shift_type not in ["morning", "afternoon"]:
        shift_type = "morning"
    
    _shift_data["is_open"] = True
    _shift_data["shift_type"] = shift_type
    _shift_data["shift_started_at"] = datetime.now().isoformat()
    
    return ProductionShiftStatus(
        is_open=True,
        shift_type=shift_type,
        shift_started_at=_shift_data["shift_started_at"],
        shift_duration_minutes=0,
        orders_started_today=_shift_data["orders_started_today"],
        orders_completed_today=_shift_data["orders_completed_today"],
        orders_in_progress=3
    )


@router.post("/shift/end", response_model=ProductionShiftReport)
def end_shift(
    current_user: ProductionUser,
) -> ProductionShiftReport:
    _reset_daily_counts()
    
    if not _shift_data["is_open"]:
        raise ValueError("No shift is currently open")
    
    started_at = datetime.fromisoformat(_shift_data["shift_started_at"])
    ended_at = datetime.now()
    duration_minutes = int((ended_at - started_at).total_seconds() / 60)
    
    orders_incomplete = _shift_data["orders_started_today"] - _shift_data["orders_completed_today"]
    
    report = ProductionShiftReport(
        shift_date=started_at.strftime("%Y-%m-%d"),
        shift_type=_shift_data["shift_type"] or "morning",
        shift_started_at=started_at.isoformat(),
        shift_ended_at=ended_at.isoformat(),
        duration_minutes=duration_minutes,
        orders_started=_shift_data["orders_started_today"],
        orders_completed=_shift_data["orders_completed_today"],
        orders_incomplete=max(0, orders_incomplete)
    )
    
    _shift_data["is_open"] = False
    _shift_data["shift_type"] = None
    _shift_data["shift_started_at"] = None
    
    return report


@router.get("/queue")
def production_queue(
    current_user: ProductionUser,
    service: Annotated[OrderService, Depends(get_order_service)],
):
    return service.list_production_queue(
        UserContext(id=current_user.id, role=current_user.role),
    )


@router.post("/orders/{order_id}/status", response_model=OrderRead)
def update_order_status(
    order_id: int,
    payload: OrderStatusUpdate,
    current_user: ProductionUser,
    service: Annotated[OrderService, Depends(get_order_service)],
) -> OrderRead:
    from app.schemas.order import OrderStatusUpdate as OrderStatusUpdateSchema
    
    _reset_daily_counts()
    
    result = service.update_order_status(
        order_id,
        OrderStatusUpdateSchema(status=payload.status),
        UserContext(id=current_user.id, role=current_user.role),
    )
    
    if payload.status == "in_production":
        _shift_data["orders_started_today"] += 1
    elif payload.status == "completed":
        _shift_data["orders_completed_today"] += 1
    
    return result
