def test_role_policies_expose_supported_roles() -> None:
    from app.domain.roles import UserRole
    from app.policies.auth_policy import can_access_role_scope

    assert can_access_role_scope(UserRole.CLIENT, UserRole.CLIENT) is True
    assert can_access_role_scope(UserRole.CLIENT, UserRole.PRODUCTION) is False


def test_order_service_creates_order_with_created_status() -> None:
    from app.core.database import SessionLocal, initialize_database, seed_demo_users
    from app.domain.order_status import OrderStatus
    from app.domain.roles import UserRole
    from app.models.branch import Branch
    from app.models.product import Product
    from app.schemas.order import OrderCreate, UserContext
    from app.services.order_service import OrderService

    initialize_database(reset=True)
    seed_demo_users()

    with SessionLocal() as session:
        session.add(
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
            )
        )
        session.add(Branch(id=1, name="Central Branch", code="CTR", city="Almaty", manager_user_id=2))
        session.commit()

        service = OrderService(session)
        order = service.create_order(
            UserContext(id=1, role=UserRole.CLIENT, branch_id=None),
            OrderCreate(product_id=1, branch_id=1, quantity=3),
        )

        assert order.status == OrderStatus.CREATED
        assert order.quantity == 3
