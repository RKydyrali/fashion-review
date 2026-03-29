from datetime import datetime, timedelta
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from app.api.deps import CurrentUser, get_order_service, require_roles
from app.domain.roles import UserRole
from app.schemas.common import Money
from app.schemas.order import OrderRead, OrderRejectRequest, UserContext
from app.services.order_service import OrderService

router = APIRouter(prefix="/franchise", tags=["franchise"])
FranchiseeUser = Annotated[CurrentUser, Depends(require_roles(UserRole.FRANCHISEE))]


class FranchiseSettingsResponse(BaseModel):
    branch_id: int
    branch_name: str
    approval_mode: str
    auto_approve_until: Optional[str] = None
    preferred_language: str


class FranchiseSettingsUpdate(BaseModel):
    approval_mode: Optional[str] = None
    preferred_language: Optional[str] = None


class DailyBreakdownItem(BaseModel):
    date: str
    revenue: int
    orders: int


class TopProductItem(BaseModel):
    product_name: str
    quantity_sold: int
    revenue: int


class SalesDataResponse(BaseModel):
    period: str
    start_date: str
    end_date: str
    total_revenue: Money
    order_count: int
    avg_order_value: Money
    daily_breakdown: list[DailyBreakdownItem]
    top_products: list[TopProductItem]


@router.get("/settings", response_model=FranchiseSettingsResponse)
def get_franchise_settings(
    current_user: FranchiseeUser,
) -> FranchiseSettingsResponse:
    branch_id = current_user.branch_id or 1
    return FranchiseSettingsResponse(
        branch_id=branch_id,
        branch_name=f"Branch #{branch_id}",
        approval_mode="manual",
        preferred_language=current_user.preferred_language,
    )


@router.patch("/settings", response_model=FranchiseSettingsResponse)
def update_franchise_settings(
    payload: FranchiseSettingsUpdate,
    current_user: FranchiseeUser,
) -> FranchiseSettingsResponse:
    branch_id = current_user.branch_id or 1
    approval_mode = payload.approval_mode or "manual"
    auto_approve_until = None
    
    if approval_mode == "auto":
        auto_approve_until = (datetime.now() + timedelta(days=1)).isoformat()
    
    return FranchiseSettingsResponse(
        branch_id=branch_id,
        branch_name=f"Branch #{branch_id}",
        approval_mode=approval_mode,
        auto_approve_until=auto_approve_until,
        preferred_language=payload.preferred_language or current_user.preferred_language,
    )


@router.get("/sales", response_model=SalesDataResponse)
def get_franchise_sales(
    current_user: FranchiseeUser,
    period: str = Query(default="week", description="Period: today, week, month, year"),
) -> SalesDataResponse:
    branch_id = current_user.branch_id or 1
    
    now = datetime.now()
    if period == "today":
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = now
    elif period == "week":
        start_date = now - timedelta(days=7)
        end_date = now
    elif period == "month":
        start_date = now - timedelta(days=30)
        end_date = now
    elif period == "year":
        start_date = now - timedelta(days=365)
        end_date = now
    else:
        start_date = now - timedelta(days=7)
        end_date = now
    
    daily_breakdown = []
    for i in range(min(7, (end_date - start_date).days or 1)):
        day = start_date + timedelta(days=i)
        daily_breakdown.append(DailyBreakdownItem(
            date=day.strftime("%Y-%m-%d"),
            revenue=50000 + (i * 10000),
            orders=2 + i,
        ))
    
    top_products = [
        TopProductItem(product_name="Classic White Shirt", quantity_sold=15, revenue=2250000),
        TopProductItem(product_name="Navy Blazer", quantity_sold=8, revenue=3200000),
        TopProductItem(product_name="Tailored Trousers", quantity_sold=12, revenue=1800000),
    ]
    
    total_revenue = sum(d.revenue for d in daily_breakdown)
    order_count = sum(d.orders for d in daily_breakdown)
    avg_order_value = total_revenue // order_count if order_count > 0 else 0
    
    return SalesDataResponse(
        period=period,
        start_date=start_date.strftime("%Y-%m-%d"),
        end_date=end_date.strftime("%Y-%m-%d"),
        total_revenue=Money(
            amount_minor=total_revenue,
            currency="KZT",
            formatted=f"{total_revenue // 100} ₸"
        ),
        order_count=order_count,
        avg_order_value=Money(
            amount_minor=avg_order_value,
            currency="KZT",
            formatted=f"{avg_order_value // 100} ₸"
        ),
        daily_breakdown=daily_breakdown,
        top_products=top_products,
    )


@router.get("/orders", response_model=list[OrderRead])
def list_franchise_orders(
    current_user: FranchiseeUser,
    service: Annotated[OrderService, Depends(get_order_service)],
) -> list[OrderRead]:
    return service.list_franchise_orders(
        UserContext(id=current_user.id, role=current_user.role),
    )


@router.post("/orders/{order_id}/approve", response_model=OrderRead)
def approve_franchise_order(
    order_id: int,
    current_user: FranchiseeUser,
    service: Annotated[OrderService, Depends(get_order_service)],
) -> OrderRead:
    from app.schemas.order import OrderStatusUpdate
    return service.update_order_status(
        order_id,
        OrderStatusUpdate(status="accepted"),
        UserContext(id=current_user.id, role=current_user.role),
    )


@router.post("/orders/{order_id}/reject", response_model=OrderRead)
def reject_franchise_order(
    order_id: int,
    payload: OrderRejectRequest,
    current_user: FranchiseeUser,
    service: Annotated[OrderService, Depends(get_order_service)],
) -> OrderRead:
    return service.reject_order(
        order_id,
        payload,
        UserContext(id=current_user.id, role=current_user.role),
    )
