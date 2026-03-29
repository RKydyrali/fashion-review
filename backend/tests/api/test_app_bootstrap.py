from fastapi.routing import APIRoute
from starlette.routing import WebSocketRoute
from fastapi.testclient import TestClient


def test_app_exposes_fastapi_entrypoint() -> None:
    from app.main import app

    assert app.title == "Fashion Pre-Order MVP API"


def test_api_v1_routes_are_registered() -> None:
    from app.main import app

    http_paths = {
        route.path
        for route in app.routes
        if isinstance(route, APIRoute)
    }

    assert "/api/v1/health" in http_paths
    assert "/api/v1/auth/me" in http_paths
    assert "/api/v1/products" in http_paths
    assert "/api/v1/sizes/recommend" in http_paths
    assert "/api/v1/try-on/sessions" in http_paths
    assert "/api/v1/try-on/sessions/{session_id}" in http_paths
    assert "/api/v1/wardrobes/capsule" in http_paths
    assert "/api/v1/client/orders" in http_paths
    assert "/api/v1/franchise/orders" in http_paths
    assert "/api/v1/franchise/orders/{order_id}/reject" in http_paths
    assert "/api/v1/production/queue" in http_paths
    assert "/api/v1/orders/{order_id}/status" in http_paths
    assert "/api/v1/orders/{order_id}/cancel" in http_paths


def test_websocket_route_is_registered() -> None:
    from app.main import app

    websocket_paths = {
        route.path
        for route in app.routes
        if isinstance(route, WebSocketRoute)
    }

    assert "/ws/updates" in websocket_paths


def test_app_startup_preserves_catalog_data_and_keeps_admin_bootstrap() -> None:
    from app.core.database import SessionLocal, initialize_database, seed_demo_catalog, seed_demo_users
    from app.main import create_app
    from app.models.product import Product
    from app.models.user import User

    initialize_database(reset=True)
    seed_demo_users()
    seed_demo_catalog()

    with TestClient(create_app()):
        pass

    with SessionLocal() as session:
        assert session.query(Product).count() > 0
        admin = session.query(User).filter(User.email == "admin@gmail.com").one_or_none()
        assert admin is not None
