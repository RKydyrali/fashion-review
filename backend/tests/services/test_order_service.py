import pytest
from fastapi import HTTPException

from app.domain.order_deadline_stage import OrderDeadlineStage
from app.domain.order_event_type import OrderEventType
from app.domain.order_status import OrderStatus
from app.domain.roles import UserRole


@pytest.fixture()
def seeded_session():
    from app.core.database import SessionLocal, initialize_database, seed_demo_users
    from app.models.branch import Branch
    from app.models.product import Product
    from app.models.user import User

    initialize_database(reset=True)
    seed_demo_users()

    with SessionLocal() as session:
        session.add_all(
            [
                Product(
                    id=1,
                    sku="DRS-001",
                    name="Silk Dress",
                    display_category="База",
                    normalized_category="top",
                    season_tags=["Лето"],
                    color="white",
                    is_available=True,
                    is_active=True,
                ),
                Product(
                    id=2,
                    sku="JKT-002",
                    name="Tailored Jacket",
                    display_category="Верхняя одежда",
                    normalized_category="outerwear",
                    season_tags=["Лето"],
                    color="black",
                    is_available=True,
                    is_active=True,
                ),
                Branch(id=1, name="Central Branch", code="CTR", city="Almaty", manager_user_id=2),
            ]
        )
        session.add(
            User(
                id=5,
                email="second-franchise@example.com",
                full_name="Second Franchise",
                hashed_password="not-used",
                role=UserRole.FRANCHISEE,
                is_active=True,
            )
        )
        session.add(
            Branch(id=2, name="North Branch", code="NTH", city="Astana", manager_user_id=5)
        )
        session.add(
            User(
                id=6,
                email="third-franchise@example.com",
                full_name="Third Franchise",
                hashed_password="not-used",
                role=UserRole.FRANCHISEE,
                is_active=True,
            )
        )
        session.add(
            Branch(id=3, name="South Branch", code="STH", city="Shymkent", manager_user_id=6)
        )
        session.commit()
        yield session


def test_client_creates_order_with_auto_assigned_branch_and_deadline(seeded_session) -> None:
    from app.schemas.order import OrderCreate, UserContext
    from app.services.order_service import OrderService

    service = OrderService(seeded_session)
    order = service.create_order(
        UserContext(id=1, role=UserRole.CLIENT, branch_id=None),
        OrderCreate(product_id=1, branch_id=None, quantity=3, delivery_city="Almaty"),
    )

    assert order.status == OrderStatus.CREATED
    assert order.client_id == 1
    assert order.branch_id == 1
    assert order.delivery_city == "Almaty"
    assert order.branch_attempt_count == 1
    assert order.current_deadline_stage == OrderDeadlineStage.BRANCH_REVIEW
    assert order.current_deadline_at is not None
    assert len(order.events) == 1
    assert order.events[0].event_type == OrderEventType.CREATED
    assert order.events[0].actor_user_id == 1
    assert order.events[0].metadata["assigned_branch_id"] == 1


def test_client_preferred_branch_is_honored_when_present(seeded_session) -> None:
    from app.schemas.order import OrderCreate, UserContext
    from app.services.order_service import OrderService

    service = OrderService(seeded_session)
    order = service.create_order(
        UserContext(id=1, role=UserRole.CLIENT, branch_id=None),
        OrderCreate(product_id=1, branch_id=2, quantity=1, delivery_city="Almaty"),
    )

    assert order.branch_id == 2
    assert order.events[0].metadata["routing_reason"] == "preferred_branch"


def test_client_city_match_falls_back_to_first_matching_branch(seeded_session) -> None:
    from app.schemas.order import OrderCreate, UserContext
    from app.services.order_service import OrderService

    service = OrderService(seeded_session)
    order = service.create_order(
        UserContext(id=1, role=UserRole.CLIENT, branch_id=None),
        OrderCreate(product_id=1, branch_id=None, quantity=1, delivery_city="Astana"),
    )

    assert order.branch_id == 2


def test_client_sees_only_own_orders(seeded_session) -> None:
    from app.schemas.order import OrderCreate, UserContext
    from app.services.order_service import OrderService

    service = OrderService(seeded_session)
    service.create_order(UserContext(id=1, role=UserRole.CLIENT, branch_id=None), OrderCreate(product_id=1, branch_id=1, quantity=1))
    service.create_order(UserContext(id=4, role=UserRole.CLIENT, branch_id=None), OrderCreate(product_id=2, branch_id=1, quantity=2))

    orders = service.list_orders_for_user(UserContext(id=1, role=UserRole.CLIENT, branch_id=None))

    assert len(orders) == 1
    assert orders[0].client_id == 1


def test_franchisee_sees_only_branch_orders(seeded_session) -> None:
    from app.schemas.order import OrderCreate, UserContext
    from app.services.order_service import OrderService

    service = OrderService(seeded_session)
    service.create_order(UserContext(id=1, role=UserRole.CLIENT, branch_id=None), OrderCreate(product_id=1, branch_id=1, quantity=1))
    service.create_order(UserContext(id=1, role=UserRole.CLIENT, branch_id=None), OrderCreate(product_id=2, branch_id=2, quantity=2))

    orders = service.list_orders_for_user(UserContext(id=2, role=UserRole.FRANCHISEE, branch_id=1))

    assert len(orders) == 1
    assert orders[0].branch_id == 1


def test_production_sees_actionable_orders_only(seeded_session) -> None:
    from app.schemas.order import OrderCreate, UserContext
    from app.services.order_service import OrderService

    service = OrderService(seeded_session)
    created = service.create_order(UserContext(id=1, role=UserRole.CLIENT, branch_id=None), OrderCreate(product_id=1, branch_id=1, quantity=1))
    accepted = service.create_order(UserContext(id=1, role=UserRole.CLIENT, branch_id=None), OrderCreate(product_id=2, branch_id=1, quantity=2))
    in_production = service.create_order(UserContext(id=1, role=UserRole.CLIENT, branch_id=None), OrderCreate(product_id=1, branch_id=1, quantity=3))

    service.update_status(accepted.id, OrderStatus.ACCEPTED, UserContext(id=2, role=UserRole.FRANCHISEE, branch_id=1))
    service.update_status(in_production.id, OrderStatus.ACCEPTED, UserContext(id=2, role=UserRole.FRANCHISEE, branch_id=1))
    service.update_status(in_production.id, OrderStatus.IN_PRODUCTION, UserContext(id=3, role=UserRole.PRODUCTION, branch_id=None))
    escalated = service.create_order(
        UserContext(id=1, role=UserRole.CLIENT, branch_id=None),
        OrderCreate(product_id=1, branch_id=1, quantity=4),
    )
    service.escalate_order(
        escalated.id,
        reason="Branch unreachable",
        current_user=UserContext(id=3, role=UserRole.PRODUCTION, branch_id=None),
    )

    orders = service.list_orders_for_user(UserContext(id=3, role=UserRole.PRODUCTION, branch_id=None))

    returned_statuses = {order.status for order in orders}
    assert OrderStatus.CREATED not in returned_statuses
    assert returned_statuses == {OrderStatus.ACCEPTED, OrderStatus.IN_PRODUCTION, OrderStatus.ESCALATED}
    assert created.id not in {order.id for order in orders}


def test_franchisee_can_accept_created_order_and_event_is_logged(seeded_session) -> None:
    from app.schemas.order import OrderCreate, UserContext
    from app.services.order_service import OrderService

    service = OrderService(seeded_session)
    order = service.create_order(UserContext(id=1, role=UserRole.CLIENT, branch_id=None), OrderCreate(product_id=1, branch_id=1, quantity=1))

    updated = service.update_status(
        order.id,
        OrderStatus.ACCEPTED,
        UserContext(id=2, role=UserRole.FRANCHISEE, branch_id=1),
        note="Approved by branch",
    )

    assert updated.status == OrderStatus.ACCEPTED
    assert len(updated.events) == 2
    assert updated.events[-1].from_status == OrderStatus.CREATED
    assert updated.events[-1].to_status == OrderStatus.ACCEPTED
    assert updated.events[-1].actor_user_id == 2
    assert updated.events[-1].event_type == OrderEventType.STATUS_CHANGED
    assert updated.events[-1].note == "Approved by branch"
    assert updated.current_deadline_stage == OrderDeadlineStage.PRODUCTION_START


def test_production_advances_accepted_order_to_in_production_then_ready(seeded_session) -> None:
    from app.schemas.order import OrderCreate, UserContext
    from app.services.order_service import OrderService

    service = OrderService(seeded_session)
    order = service.create_order(UserContext(id=1, role=UserRole.CLIENT, branch_id=None), OrderCreate(product_id=1, branch_id=1, quantity=1))
    service.update_status(order.id, OrderStatus.ACCEPTED, UserContext(id=2, role=UserRole.FRANCHISEE, branch_id=1))

    in_production = service.update_status(
        order.id,
        OrderStatus.IN_PRODUCTION,
        UserContext(id=3, role=UserRole.PRODUCTION, branch_id=None),
    )
    ready = service.update_status(
        order.id,
        OrderStatus.READY,
        UserContext(id=3, role=UserRole.PRODUCTION, branch_id=None),
    )

    assert in_production.status == OrderStatus.IN_PRODUCTION
    assert ready.status == OrderStatus.READY
    assert [event.to_status for event in ready.events] == [
        OrderStatus.CREATED,
        OrderStatus.ACCEPTED,
        OrderStatus.IN_PRODUCTION,
        OrderStatus.READY,
    ]
    assert in_production.current_deadline_stage == OrderDeadlineStage.PRODUCTION_COMPLETION
    assert ready.current_deadline_stage is None


def test_invalid_transition_is_rejected(seeded_session) -> None:
    from app.schemas.order import OrderCreate, UserContext
    from app.services.order_service import OrderService

    service = OrderService(seeded_session)
    order = service.create_order(UserContext(id=1, role=UserRole.CLIENT, branch_id=None), OrderCreate(product_id=1, branch_id=1, quantity=1))

    with pytest.raises(HTTPException) as exc_info:
        service.update_status(
            order.id,
            OrderStatus.READY,
            UserContext(id=2, role=UserRole.FRANCHISEE, branch_id=1),
        )

    assert exc_info.value.status_code == 400


def test_wrong_role_transition_is_rejected(seeded_session) -> None:
    from app.schemas.order import OrderCreate, UserContext
    from app.services.order_service import OrderService

    service = OrderService(seeded_session)
    order = service.create_order(UserContext(id=1, role=UserRole.CLIENT, branch_id=None), OrderCreate(product_id=1, branch_id=1, quantity=1))
    service.update_status(order.id, OrderStatus.ACCEPTED, UserContext(id=2, role=UserRole.FRANCHISEE, branch_id=1))

    with pytest.raises(HTTPException) as exc_info:
        service.update_status(
            order.id,
            OrderStatus.IN_PRODUCTION,
            UserContext(id=2, role=UserRole.FRANCHISEE, branch_id=1),
        )

    assert exc_info.value.status_code == 403


def test_franchise_rejection_reassigns_order_to_next_branch(seeded_session) -> None:
    from app.schemas.order import OrderCreate, OrderRejectRequest, UserContext
    from app.services.order_service import OrderService

    service = OrderService(seeded_session)
    order = service.create_order(
        UserContext(id=1, role=UserRole.CLIENT, branch_id=None),
        OrderCreate(product_id=1, branch_id=1, quantity=1),
    )

    updated = service.reject_order(
        order.id,
        OrderRejectRequest(note="Branch is full"),
        UserContext(id=2, role=UserRole.FRANCHISEE, branch_id=1),
    )

    assert updated.status == OrderStatus.CREATED
    assert updated.branch_id == 2
    assert updated.branch_attempt_count == 2
    assert updated.current_deadline_stage == OrderDeadlineStage.BRANCH_REVIEW
    assert updated.events[-2].event_type == OrderEventType.REJECTED
    assert updated.events[-1].event_type == OrderEventType.REASSIGNED
    assert updated.events[-1].metadata["previous_branch_id"] == 1
    assert updated.events[-1].metadata["assigned_branch_id"] == 2


def test_rejection_escalates_after_max_branch_attempts(seeded_session) -> None:
    from app.schemas.order import OrderCreate, OrderRejectRequest, UserContext
    from app.services.order_service import OrderService

    service = OrderService(seeded_session)
    order = service.create_order(
        UserContext(id=1, role=UserRole.CLIENT, branch_id=None),
        OrderCreate(product_id=1, branch_id=1, quantity=1),
    )

    service.reject_order(
        order.id,
        OrderRejectRequest(note="Central branch cannot take it"),
        UserContext(id=2, role=UserRole.FRANCHISEE, branch_id=1),
    )
    service.reject_order(
        order.id,
        OrderRejectRequest(note="North branch cannot take it"),
        UserContext(id=5, role=UserRole.FRANCHISEE, branch_id=2),
    )
    escalated = service.reject_order(
        order.id,
        OrderRejectRequest(note="South branch cannot take it"),
        UserContext(id=6, role=UserRole.FRANCHISEE, branch_id=3),
    )

    assert escalated.status == OrderStatus.ESCALATED
    assert escalated.branch_attempt_count == 3
    assert escalated.escalation_reason == "No eligible branches remain"
    assert escalated.events[-1].event_type == OrderEventType.ESCALATED


def test_client_can_cancel_before_production(seeded_session) -> None:
    from app.schemas.order import OrderCancelRequest, OrderCreate, UserContext
    from app.services.order_service import OrderService

    service = OrderService(seeded_session)
    order = service.create_order(
        UserContext(id=1, role=UserRole.CLIENT, branch_id=None),
        OrderCreate(product_id=1, branch_id=1, quantity=1),
    )

    cancelled = service.cancel_order(
        order.id,
        OrderCancelRequest(reason="Changed my mind"),
        UserContext(id=1, role=UserRole.CLIENT, branch_id=None),
    )

    assert cancelled.status == OrderStatus.CANCELLED
    assert cancelled.cancellation_reason == "Changed my mind"
    assert cancelled.events[-1].event_type == OrderEventType.CANCELLED


def test_client_cannot_cancel_after_production_starts(seeded_session) -> None:
    from app.schemas.order import OrderCancelRequest, OrderCreate, UserContext
    from app.services.order_service import OrderService

    service = OrderService(seeded_session)
    order = service.create_order(
        UserContext(id=1, role=UserRole.CLIENT, branch_id=None),
        OrderCreate(product_id=1, branch_id=1, quantity=1),
    )
    service.update_status(order.id, OrderStatus.ACCEPTED, UserContext(id=2, role=UserRole.FRANCHISEE, branch_id=1))
    service.update_status(order.id, OrderStatus.IN_PRODUCTION, UserContext(id=3, role=UserRole.PRODUCTION, branch_id=None))

    with pytest.raises(HTTPException) as exc_info:
        service.cancel_order(
            order.id,
            OrderCancelRequest(reason="Too late"),
            UserContext(id=1, role=UserRole.CLIENT, branch_id=None),
        )

    assert exc_info.value.status_code == 403


def test_reject_requires_assigned_franchisee_and_note(seeded_session) -> None:
    from app.schemas.order import OrderCreate, OrderRejectRequest, UserContext
    from app.services.order_service import OrderService

    service = OrderService(seeded_session)
    order = service.create_order(
        UserContext(id=1, role=UserRole.CLIENT, branch_id=None),
        OrderCreate(product_id=1, branch_id=1, quantity=1),
    )

    with pytest.raises(HTTPException) as exc_info:
        service.reject_order(
            order.id,
            OrderRejectRequest(note="Wrong branch actor"),
            UserContext(id=5, role=UserRole.FRANCHISEE, branch_id=2),
        )

    assert exc_info.value.status_code == 403

    with pytest.raises(HTTPException) as exc_info:
        service.reject_order(
            order.id,
            OrderRejectRequest(note=""),
            UserContext(id=2, role=UserRole.FRANCHISEE, branch_id=1),
        )

    assert exc_info.value.status_code == 400


def test_sla_sweep_reassigns_overdue_created_order(seeded_session) -> None:
    from app.schemas.order import OrderCreate, UserContext
    from app.services.order_service import OrderService
    from app.services.order_sla_service import OrderSLAService

    service = OrderService(seeded_session)
    order = service.create_order(
        UserContext(id=1, role=UserRole.CLIENT, branch_id=None),
        OrderCreate(product_id=1, branch_id=1, quantity=1),
    )
    order_model = service.orders.get_by_id(order.id)
    order_model.current_deadline_at = order_model.current_deadline_at.replace(year=2000)
    seeded_session.commit()

    sweep_service = OrderSLAService(seeded_session, order_service=service)
    updated_orders = sweep_service.run_due_actions()

    assert {updated.id for updated in updated_orders} == {order.id}
    refreshed = service.orders.get_by_id(order.id)
    assert refreshed.branch_id == 2
    assert refreshed.branch_attempt_count == 2
    assert refreshed.events[-2].event_type == OrderEventType.SLA_MISSED
    assert refreshed.events[-1].event_type == OrderEventType.REASSIGNED


def test_sla_sweep_escalates_overdue_production_work(seeded_session) -> None:
    from app.schemas.order import OrderCreate, UserContext
    from app.services.order_service import OrderService
    from app.services.order_sla_service import OrderSLAService

    service = OrderService(seeded_session)
    order = service.create_order(
        UserContext(id=1, role=UserRole.CLIENT, branch_id=None),
        OrderCreate(product_id=1, branch_id=1, quantity=1),
    )
    service.update_status(order.id, OrderStatus.ACCEPTED, UserContext(id=2, role=UserRole.FRANCHISEE, branch_id=1))
    order_model = service.orders.get_by_id(order.id)
    order_model.current_deadline_at = order_model.current_deadline_at.replace(year=2000)
    seeded_session.commit()

    sweep_service = OrderSLAService(seeded_session, order_service=service)
    updated_orders = sweep_service.run_due_actions()

    assert {updated.id for updated in updated_orders} == {order.id}
    refreshed = service.orders.get_by_id(order.id)
    assert refreshed.status == OrderStatus.ESCALATED
    assert refreshed.escalation_reason == "SLA deadline missed during production_start"
    assert refreshed.events[-2].event_type == OrderEventType.SLA_MISSED
    assert refreshed.events[-1].event_type == OrderEventType.ESCALATED
