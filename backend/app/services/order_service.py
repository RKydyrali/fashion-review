from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.domain.order_deadline_stage import OrderDeadlineStage
from app.domain.order_event_type import OrderEventType
from app.domain.order_status import OrderStatus
from app.domain.roles import UserRole
from app.models.branch import Branch
from app.models.order import Order
from app.models.product import Product
from app.repositories.order_event_repository import OrderEventRepository
from app.repositories.order_repository import OrderRepository
from app.schemas.order import (
    OrderCancelRequest,
    OrderCreate,
    OrderEventRead,
    OrderRead,
    OrderRejectRequest,
    OrderStatusUpdate,
    UserContext,
)
from app.services.product_localization import money, price_breakdown
from app.websocket.publisher import NullOrderEventPublisher, OrderEventPublisher


class OrderService:
    _TRANSITIONS: dict[OrderStatus, OrderStatus] = {
        OrderStatus.CREATED: OrderStatus.ACCEPTED,
        OrderStatus.ACCEPTED: OrderStatus.IN_PRODUCTION,
        OrderStatus.IN_PRODUCTION: OrderStatus.READY,
        OrderStatus.READY: OrderStatus.PICKED_UP,
    }

    def __init__(self, session: Session, event_publisher: OrderEventPublisher | None = None) -> None:
        self.session = session
        self.settings = get_settings()
        self.orders = OrderRepository(session)
        self.events = OrderEventRepository(session)
        self.event_publisher = event_publisher or NullOrderEventPublisher()

    def create_order(self, current_user: UserContext, payload: OrderCreate) -> OrderRead:
        if current_user.role != UserRole.CLIENT:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only clients can create orders")

        product = self._require_product(payload.product_id)
        branch, routing_reason = self._select_branch(
            preferred_branch_id=payload.branch_id,
            delivery_city=payload.delivery_city,
            excluded_branch_ids=set(),
        )
        deadline_at = self._deadline_at(OrderDeadlineStage.BRANCH_REVIEW)

        order = self.orders.create(
            payload,
            client_id=current_user.id,
            branch_id=branch.id,
            delivery_city=payload.delivery_city,
            branch_attempt_count=1,
            current_deadline_at=deadline_at,
            current_deadline_stage=OrderDeadlineStage.BRANCH_REVIEW,
        )
        pricing = price_breakdown(product.base_price_minor, payload.size_label or "M", product.currency)
        order.unit_price_minor = pricing.total_price.amount_minor
        order.tailoring_adjustment_minor = pricing.tailoring_adjustment.amount_minor
        order.total_price_minor = pricing.total_price.amount_minor * payload.quantity
        order.currency = product.currency
        self._record_event(
            order_id=order.id,
            actor_user_id=current_user.id,
            event_type=OrderEventType.CREATED,
            from_status=None,
            to_status=OrderStatus.CREATED,
            metadata={
                "assigned_branch_id": branch.id,
                "preferred_branch_id": payload.branch_id,
                "routing_reason": routing_reason,
            },
        )
        self.session.commit()
        order_read = self._to_read_model(order.id)
        self.event_publisher.publish_order_created(order_read)
        return order_read

    def list_client_orders(self, current_user: UserContext) -> list[OrderRead]:
        return self.list_orders_for_user(current_user)

    def list_franchise_orders(self, current_user: UserContext) -> list[OrderRead]:
        orders = self.list_orders_for_user(current_user)
        return [order for order in orders if order.status in {OrderStatus.CREATED, OrderStatus.ACCEPTED}]

    def list_production_queue(self, current_user: UserContext) -> list[OrderRead]:
        return self.list_orders_for_user(current_user)

    def list_orders_for_user(self, current_user: UserContext, branch_id: int | None = None) -> list[OrderRead]:
        if current_user.role == UserRole.CLIENT:
            orders = self.orders.list_for_client(current_user.id)
        elif current_user.role == UserRole.FRANCHISEE:
            resolved_branch_id = branch_id or current_user.branch_id or self._resolve_managed_branch_id(current_user.id)
            orders = self.orders.list_for_branch(resolved_branch_id)
        elif current_user.role == UserRole.PRODUCTION:
            orders = self.orders.list_by_statuses(
                (OrderStatus.ACCEPTED, OrderStatus.IN_PRODUCTION, OrderStatus.READY, OrderStatus.ESCALATED)
            )
        else:
            orders = []

        return [self.serialize_order(order) for order in orders]


    def update_order_status(
        self,
        order_id: int,
        payload: OrderStatusUpdate,
        current_user: UserContext,
    ) -> OrderRead:
        return self.update_status(
            order_id,
            payload.status,
            current_user,
            note=payload.note,
        )

    def update_status(
        self,
        order_id: int,
        new_status: OrderStatus,
        current_user: UserContext,
        note: str | None = None,
    ) -> OrderRead:
        order = self._require_order(order_id)

        self._validate_transition(order.status, new_status)
        self._enforce_transition_permission(order.branch_id, order.status, new_status, current_user)

        previous_status = order.status
        order.status = new_status
        order.escalation_reason = None
        if new_status == OrderStatus.ACCEPTED:
            self._set_deadline(order, OrderDeadlineStage.PRODUCTION_START)
        elif new_status == OrderStatus.IN_PRODUCTION:
            self._set_deadline(order, OrderDeadlineStage.PRODUCTION_COMPLETION)
        else:
            self._clear_deadline(order)
        self.orders.save(order)
        self._record_event(
            order_id=order.id,
            actor_user_id=current_user.id,
            event_type=OrderEventType.STATUS_CHANGED,
            from_status=previous_status,
            to_status=new_status,
            note=note,
        )
        self.session.commit()
        order_read = self._to_read_model(order.id)
        self.event_publisher.publish_order_status_changed(
            order_read,
            previous_status=previous_status,
            note=note,
        )
        return order_read

    def reject_order(
        self,
        order_id: int,
        payload: OrderRejectRequest,
        current_user: UserContext,
    ) -> OrderRead:
        note = payload.note.strip()
        if not note:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Rejection note is required")

        order = self._require_order(order_id)
        self._enforce_branch_actor(order, current_user)
        if order.status not in {OrderStatus.CREATED, OrderStatus.ACCEPTED}:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Order cannot be rejected")

        self._record_event(
            order_id=order.id,
            actor_user_id=current_user.id,
            event_type=OrderEventType.REJECTED,
            from_status=order.status,
            to_status=order.status,
            note=note,
            metadata={"rejected_branch_id": order.branch_id},
        )
        return self._reassign_or_escalate(order, actor_user_id=current_user.id, note=note)

    def cancel_order(
        self,
        order_id: int,
        payload: OrderCancelRequest,
        current_user: UserContext,
    ) -> OrderRead:
        reason = payload.reason.strip()
        if not reason:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cancellation reason is required")

        order = self._require_order(order_id)
        self._enforce_cancellation_permission(order, current_user)

        previous_status = order.status
        order.status = OrderStatus.CANCELLED
        order.cancellation_reason = reason
        self._clear_deadline(order)
        self.orders.save(order)
        self._record_event(
            order_id=order.id,
            actor_user_id=current_user.id,
            event_type=OrderEventType.CANCELLED,
            from_status=previous_status,
            to_status=OrderStatus.CANCELLED,
            note=reason,
        )
        self.session.commit()
        order_read = self._to_read_model(order.id)
        self.event_publisher.publish_order_status_changed(
            order_read,
            previous_status=previous_status,
            note=reason,
        )
        return order_read

    def escalate_order(
        self,
        order_id: int,
        *,
        reason: str,
        current_user: UserContext,
    ) -> OrderRead:
        if current_user.role != UserRole.PRODUCTION:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only production can escalate orders")
        order = self._require_order(order_id)
        return self._escalate_existing_order(order, reason=reason.strip() or "Escalated", actor_user_id=current_user.id)

    def process_sla_expiration(self, order_id: int, *, now: datetime | None = None) -> OrderRead | None:
        order = self._require_order(order_id)
        effective_now = self._normalize_datetime(now or datetime.now(timezone.utc))
        if order.current_deadline_at is None or self._normalize_datetime(order.current_deadline_at) > effective_now:
            return None
        if order.status not in {OrderStatus.CREATED, OrderStatus.ACCEPTED, OrderStatus.IN_PRODUCTION}:
            return None

        stage = order.current_deadline_stage.value if order.current_deadline_stage is not None else "unknown"
        reason = f"SLA deadline missed during {stage}"
        self._record_event(
            order_id=order.id,
            actor_user_id=None,
            event_type=OrderEventType.SLA_MISSED,
            from_status=order.status,
            to_status=order.status,
            note=reason,
            metadata={"deadline_stage": stage},
        )
        if order.status == OrderStatus.CREATED:
            return self._reassign_or_escalate(order, actor_user_id=None, note=reason)
        return self._escalate_existing_order(order, reason=reason, actor_user_id=None)

    def _validate_transition(self, current_status: OrderStatus, new_status: OrderStatus) -> None:
        allowed_next_status = self._TRANSITIONS.get(current_status)
        if allowed_next_status != new_status:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid order status transition")

    def _enforce_transition_permission(
        self,
        order_branch_id: int,
        current_status: OrderStatus,
        new_status: OrderStatus,
        current_user: UserContext,
    ) -> None:
        if current_status == OrderStatus.CREATED and new_status == OrderStatus.ACCEPTED:
            self._enforce_branch_user_for_branch(order_branch_id, current_user)
            return

        if current_status in {OrderStatus.ACCEPTED, OrderStatus.IN_PRODUCTION} and new_status in {
            OrderStatus.IN_PRODUCTION,
            OrderStatus.READY,
        }:
            if current_user.role != UserRole.PRODUCTION:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only production can advance this order")
            return

        if current_status == OrderStatus.READY and new_status == OrderStatus.PICKED_UP:
            if current_user.role != UserRole.CLIENT:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only client can pickup their order")
            return

        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

    def _enforce_cancellation_permission(self, order: Order, current_user: UserContext) -> None:
        if current_user.role == UserRole.CLIENT and current_user.id == order.client_id:
            if order.status in {OrderStatus.CREATED, OrderStatus.ACCEPTED}:
                return
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Client cannot cancel this order now")

        if current_user.role == UserRole.FRANCHISEE:
            self._enforce_branch_user_for_branch(order.branch_id, current_user)
            if order.status in {OrderStatus.CREATED, OrderStatus.ACCEPTED}:
                return
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Franchisee cannot cancel this order now")

        if current_user.role == UserRole.PRODUCTION and order.status in {
            OrderStatus.ACCEPTED,
            OrderStatus.IN_PRODUCTION,
            OrderStatus.ESCALATED,
        }:
            return

        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

    def _enforce_branch_actor(self, order: Order, current_user: UserContext) -> None:
        if order.status not in {OrderStatus.CREATED, OrderStatus.ACCEPTED}:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Order is not branch-owned")
        self._enforce_branch_user_for_branch(order.branch_id, current_user)

    def _enforce_branch_user_for_branch(self, order_branch_id: int, current_user: UserContext) -> None:
        if current_user.role != UserRole.FRANCHISEE:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only franchisees can manage this order")
        managed_branch_id = current_user.branch_id or self._resolve_managed_branch_id(current_user.id)
        if managed_branch_id != order_branch_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Franchisee cannot manage this branch")

    def _reassign_or_escalate(self, order: Order, *, actor_user_id: int | None, note: str) -> OrderRead:
        previous_status = order.status
        previous_branch_id = order.branch_id
        if order.branch_attempt_count >= self.settings.max_branch_assignment_attempts:
            return self._escalate_existing_order(order, reason="No eligible branches remain", actor_user_id=actor_user_id)

        preferred_branch_id = self._preferred_branch_id_for(order)
        selected = self._try_select_branch(
            preferred_branch_id=preferred_branch_id,
            delivery_city=order.delivery_city,
            excluded_branch_ids=self._tried_branch_ids(order),
        )
        if selected is None:
            return self._escalate_existing_order(order, reason="No eligible branches remain", actor_user_id=actor_user_id)

        branch, routing_reason = selected
        order.branch_id = branch.id
        order.branch_attempt_count += 1
        order.status = OrderStatus.CREATED
        order.escalation_reason = None
        self._set_deadline(order, OrderDeadlineStage.BRANCH_REVIEW)
        self.orders.save(order)
        self._record_event(
            order_id=order.id,
            actor_user_id=actor_user_id,
            event_type=OrderEventType.REASSIGNED,
            from_status=previous_status,
            to_status=order.status,
            note=note,
            metadata={
                "previous_branch_id": previous_branch_id,
                "assigned_branch_id": branch.id,
                "routing_reason": routing_reason,
            },
        )
        self.session.commit()
        order_read = self._to_read_model(order.id)
        if previous_status == OrderStatus.CREATED:
            self.event_publisher.publish_order_reassigned(
                order_read,
                previous_branch_id=previous_branch_id,
                note=note,
            )
        else:
            self.event_publisher.publish_order_status_changed(
                order_read,
                previous_status=previous_status,
                note=note,
            )
        return order_read

    def _escalate_existing_order(self, order: Order, *, reason: str, actor_user_id: int | None) -> OrderRead:
        previous_status = order.status
        order.status = OrderStatus.ESCALATED
        order.escalation_reason = reason
        self._clear_deadline(order)
        self.orders.save(order)
        self._record_event(
            order_id=order.id,
            actor_user_id=actor_user_id,
            event_type=OrderEventType.ESCALATED,
            from_status=previous_status,
            to_status=OrderStatus.ESCALATED,
            note=reason,
        )
        self.session.commit()
        order_read = self._to_read_model(order.id)
        self.event_publisher.publish_order_status_changed(
            order_read,
            previous_status=previous_status,
            note=reason,
        )
        return order_read

    def _record_event(
        self,
        *,
        order_id: int,
        actor_user_id: int | None,
        event_type: OrderEventType,
        from_status: OrderStatus | None,
        to_status: OrderStatus,
        note: str | None = None,
        metadata: dict[str, object] | None = None,
    ) -> None:
        self.events.create(
            order_id=order_id,
            actor_user_id=actor_user_id,
            event_type=event_type,
            from_status=from_status,
            to_status=to_status,
            note=note,
            metadata=metadata,
        )

    def _set_deadline(self, order: Order, stage: OrderDeadlineStage) -> None:
        order.current_deadline_stage = stage
        order.current_deadline_at = self._deadline_at(stage)

    def _clear_deadline(self, order: Order) -> None:
        order.current_deadline_stage = None
        order.current_deadline_at = None

    def _deadline_at(self, stage: OrderDeadlineStage) -> datetime:
        minutes = {
            OrderDeadlineStage.BRANCH_REVIEW: self.settings.branch_review_sla_minutes,
            OrderDeadlineStage.PRODUCTION_START: self.settings.production_start_sla_minutes,
            OrderDeadlineStage.PRODUCTION_COMPLETION: self.settings.production_completion_sla_minutes,
        }[stage]
        return self._normalize_datetime(datetime.now(timezone.utc) + timedelta(minutes=minutes))

    def _preferred_branch_id_for(self, order: Order) -> int | None:
        for event in order.events:
            if event.event_type == OrderEventType.CREATED and event.event_metadata:
                preferred_branch_id = event.event_metadata.get("preferred_branch_id")
                if isinstance(preferred_branch_id, int):
                    return preferred_branch_id
        return None

    def _tried_branch_ids(self, order: Order) -> set[int]:
        tried_branch_ids = {order.branch_id}
        for event in order.events:
            if event.event_metadata is None:
                continue
            assigned_branch_id = event.event_metadata.get("assigned_branch_id")
            if isinstance(assigned_branch_id, int):
                tried_branch_ids.add(assigned_branch_id)
        return tried_branch_ids

    def _select_branch(
        self,
        *,
        preferred_branch_id: int | None,
        delivery_city: str | None,
        excluded_branch_ids: set[int],
    ) -> tuple[Branch, str]:
        selected = self._try_select_branch(
            preferred_branch_id=preferred_branch_id,
            delivery_city=delivery_city,
            excluded_branch_ids=excluded_branch_ids,
        )
        if selected is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No branches available")
        return selected

    def _try_select_branch(
        self,
        *,
        preferred_branch_id: int | None,
        delivery_city: str | None,
        excluded_branch_ids: set[int],
    ) -> tuple[Branch, str] | None:
        branches = self._list_branches(excluded_branch_ids)
        if preferred_branch_id is not None:
            preferred_branch = self._require_branch(preferred_branch_id)
            if preferred_branch.id not in excluded_branch_ids:
                return preferred_branch, "preferred_branch"

        normalized_city = self._normalize_text(delivery_city)
        if normalized_city:
            for branch in branches:
                if self._normalize_text(branch.city) == normalized_city:
                    return branch, "delivery_city"

        if branches:
            return branches[0], "first_available"
        return None

    def _list_branches(self, excluded_branch_ids: set[int]) -> list[Branch]:
        statement = select(Branch).order_by(Branch.id)
        branches = list(self.session.scalars(statement))
        return [branch for branch in branches if branch.id not in excluded_branch_ids]

    def _require_product(self, product_id: int) -> Product:
        product = self.session.get(Product, product_id)
        if product is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
        return product

    def _require_branch(self, branch_id: int) -> Branch:
        branch = self.session.get(Branch, branch_id)
        if branch is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Branch not found")
        return branch

    def _resolve_managed_branch_id(self, user_id: int) -> int:
        statement = select(Branch.id).where(Branch.manager_user_id == user_id).limit(1)
        branch_id = self.session.scalar(statement)
        if branch_id is None:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Franchisee branch not found")
        return branch_id

    def _require_order(self, order_id: int) -> Order:
        order = self.orders.get_by_id(order_id)
        if order is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
        return order

    def _normalize_text(self, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip().lower()
        return normalized or None

    def _normalize_datetime(self, value: datetime) -> datetime:
        if value.tzinfo is None:
            return value
        return value.astimezone(timezone.utc).replace(tzinfo=None)

    def _to_read_model(self, order_id: int) -> OrderRead:
        order = self.orders.get_by_id(order_id)
        if order is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
        return self.serialize_order(order)

    def serialize_order(self, order: Order) -> OrderRead:
        data = {
            "id": order.id,
            "client_id": order.client_id,
            "product_id": order.product_id,
            "branch_id": order.branch_id,
            "preorder_batch_id": order.preorder_batch_id,
            "delivery_city": order.delivery_city,
            "size_label": order.size_label,
            "quantity": order.quantity,
            "unit_price": money(order.unit_price_minor, order.currency),
            "price_breakdown": price_breakdown(order.product.base_price_minor, order.size_label, order.currency) if order.size_label and order.product else None,
            "line_total": money(order.total_price_minor, order.currency),
            "branch_attempt_count": order.branch_attempt_count,
            "current_deadline_at": order.current_deadline_at,
            "current_deadline_stage": order.current_deadline_stage,
            "cancellation_reason": order.cancellation_reason,
            "escalation_reason": order.escalation_reason,
            "status": order.status,
            "events": [OrderEventRead.model_validate(e) for e in order.events],
            "product": {
                "id": order.product.id,
                "name": order.product.name,
                "hero_image_url": order.product.hero_image_url,
                "color": order.product.color,
            } if order.product else None,
        }
        return OrderRead.model_validate(data)
