from app.domain.order_status import OrderStatus


def test_order_repository_creates_and_lists_orders() -> None:
    from app.core.database import SessionLocal, initialize_database, seed_demo_users
    from app.domain.order_deadline_stage import OrderDeadlineStage
    from app.models.branch import Branch
    from app.models.product import Product
    from app.repositories.order_repository import OrderRepository
    from app.schemas.order import OrderCreate

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

        repository = OrderRepository(session)
        created = repository.create(
            OrderCreate(product_id=1, branch_id=None, quantity=2, delivery_city="Almaty"),
            client_id=1,
            branch_id=1,
            delivery_city="Almaty",
            branch_attempt_count=1,
            current_deadline_stage=OrderDeadlineStage.BRANCH_REVIEW,
        )
        session.commit()

        assert created.id == 1
        assert created.status == OrderStatus.CREATED
        assert created.branch_id == 1
        assert created.delivery_city == "Almaty"
        assert created.branch_attempt_count == 1
        assert created.current_deadline_stage == OrderDeadlineStage.BRANCH_REVIEW
        assert repository.list_for_client(1)[0].product_id == 1
