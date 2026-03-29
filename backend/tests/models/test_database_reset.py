def test_initialize_database_reset_can_be_repeated_before_app_startup_without_duplicate_seed_failures() -> None:
    from fastapi.testclient import TestClient
    from sqlalchemy import select

    from app.core.database import SessionLocal, initialize_database, seed_demo_catalog, seed_demo_size_charts, seed_demo_users
    from app.main import create_app
    from app.models.product import Product
    from app.models.user import User

    initialize_database(reset=True)
    seed_demo_users()
    seed_demo_catalog()
    seed_demo_size_charts()

    initialize_database(reset=True)
    seed_demo_users()
    seed_demo_catalog()
    seed_demo_size_charts()

    with TestClient(create_app()) as client:
        health = client.get("/api/v1/health")

    assert health.status_code == 200

    with SessionLocal() as session:
        user_count = len(list(session.scalars(select(User.id))))
        product_count = len(list(session.scalars(select(Product.id))))

    assert user_count == 5
    assert product_count == 5
