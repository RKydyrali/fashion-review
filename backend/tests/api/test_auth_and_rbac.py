from datetime import timedelta

import pytest
from fastapi.testclient import TestClient

from app.domain.roles import UserRole


@pytest.fixture()
def client() -> TestClient:
    from app.core.database import SessionLocal
    from app.core.database import initialize_database, seed_demo_catalog, seed_demo_users
    from app.core.security import get_password_hash
    from app.domain.roles import UserRole
    from app.main import create_app
    from app.models.branch import Branch
    from app.models.user import User

    initialize_database(reset=True)
    seed_demo_users()
    seed_demo_catalog()
    with SessionLocal() as session:
        session.add(
            User(
                id=5,
                email="second-franchise@example.com",
                full_name="Second Franchise",
                hashed_password=get_password_hash("secondfranchisepass123"),
                role=UserRole.FRANCHISEE,
                is_active=True,
            )
        )
        session.add(
            Branch(id=2, name="North Branch", code="NTH", city="Astana", manager_user_id=5)
        )
        session.commit()

    with TestClient(create_app()) as test_client:
        yield test_client


def login(client: TestClient, username: str, password: str) -> dict:
    response = client.post(
        "/api/v1/auth/login",
        data={"username": username, "password": password},
    )
    return {
        "status_code": response.status_code,
        "body": response.json(),
    }


def test_login_returns_bearer_token_with_expected_claims(client: TestClient) -> None:
    from app.core.security import decode_access_token

    result = login(client, "client@example.com", "clientpass123")

    assert result["status_code"] == 200
    assert result["body"]["token_type"] == "bearer"

    claims = decode_access_token(result["body"]["access_token"])
    assert claims.sub == "1"
    assert claims.role == UserRole.CLIENT
    assert claims.exp is not None


def test_login_rejects_unknown_email(client: TestClient) -> None:
    result = login(client, "missing@example.com", "whatever")

    assert result["status_code"] == 401


def test_login_rejects_wrong_password(client: TestClient) -> None:
    result = login(client, "client@example.com", "wrong-password")

    assert result["status_code"] == 401


def test_login_rejects_inactive_user(client: TestClient) -> None:
    result = login(client, "inactive@example.com", "inactivepass123")

    assert result["status_code"] == 401


def test_auth_me_returns_authenticated_user_not_hardcoded_fallback(client: TestClient) -> None:
    token = login(client, "franchise@example.com", "franchisepass123")["body"]["access_token"]

    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["email"] == "franchise@example.com"
    assert response.json()["role"] == UserRole.FRANCHISEE.value
    assert response.json()["preferred_language"] == "kk"
    assert response.json()["body_profile"] is None


def test_auth_me_returns_body_profile_when_user_has_progressive_profile_data(client: TestClient) -> None:
    from app.core.database import SessionLocal
    from app.models.user import User

    with SessionLocal() as session:
        user = session.get(User, 2)
        assert user is not None
        user.height_cm = 172.0
        user.chest_cm = 92.0
        user.preferred_fit = "regular"
        user.alpha_size = "M"
        session.commit()

    token = login(client, "franchise@example.com", "franchisepass123")["body"]["access_token"]

    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["body_profile"] == {
        "height_cm": 172.0,
        "weight_kg": None,
        "chest_cm": 92.0,
        "waist_cm": None,
        "hips_cm": None,
        "preferred_fit": "regular",
        "alpha_size": "M",
        "top_size": None,
        "bottom_size": None,
        "dress_size": None,
    }


def test_patch_body_profile_updates_only_submitted_fields(client: TestClient) -> None:
    token = login(client, "client@example.com", "clientpass123")["body"]["access_token"]

    response = client.patch(
        "/api/v1/auth/me/body-profile",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "height_cm": 168.0,
            "preferred_fit": "oversized",
            "alpha_size": "S",
        },
    )

    assert response.status_code == 200
    assert response.json()["body_profile"] == {
        "height_cm": 168.0,
        "weight_kg": None,
        "chest_cm": None,
        "waist_cm": None,
        "hips_cm": None,
        "preferred_fit": "oversized",
        "alpha_size": "S",
        "top_size": None,
        "bottom_size": None,
        "dress_size": None,
    }


def test_patch_body_profile_clears_fields_when_explicit_null_is_sent(client: TestClient) -> None:
    from app.core.database import SessionLocal
    from app.models.user import User

    with SessionLocal() as session:
        user = session.get(User, 1)
        assert user is not None
        user.height_cm = 170.0
        user.waist_cm = 72.0
        user.top_size = "M"
        session.commit()

    token = login(client, "client@example.com", "clientpass123")["body"]["access_token"]

    response = client.patch(
        "/api/v1/auth/me/body-profile",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "height_cm": None,
            "waist_cm": None,
            "top_size": None,
        },
    )

    assert response.status_code == 200
    assert response.json()["body_profile"] is None


def test_products_route_returns_catalog_for_real_user_flow(client: TestClient) -> None:
    response = client.get("/api/v1/products")

    assert response.status_code == 200
    assert response.json()
    assert response.json()[0]["sku"] == "TOP-001"
    assert response.json()[0]["name"] == "Шелковый топ"
    assert response.json()[0]["display_category"] == "База"
    assert response.json()[0]["normalized_category"] == "top"


def test_products_route_uses_authenticated_user_preferred_language_when_header_missing(client: TestClient) -> None:
    token = login(client, "franchise@example.com", "franchisepass123")["body"]["access_token"]

    response = client.get(
        "/api/v1/products",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()[0]["name"] == "Жібек топ"
    assert response.json()[0]["display_category"] == "Негізгі киім"


def test_accept_language_header_takes_precedence_over_user_preference(client: TestClient) -> None:
    token = login(client, "franchise@example.com", "franchisepass123")["body"]["access_token"]

    response = client.get(
        "/api/v1/products",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept-Language": "en-US,en;q=0.9",
        },
    )

    assert response.status_code == 200
    assert response.json()[0]["name"] == "Silk Shell Top"
    assert response.json()[0]["display_category"] == "Basics"


def test_client_is_denied_from_franchise_and_production_routes(client: TestClient) -> None:
    token = login(client, "client@example.com", "clientpass123")["body"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    franchise_response = client.get("/api/v1/franchise/orders", headers=headers)
    production_response = client.get("/api/v1/production/queue", headers=headers)

    assert franchise_response.status_code == 403
    assert production_response.status_code == 403


def test_franchisee_can_access_franchise_route_but_not_production_route(client: TestClient) -> None:
    token = login(client, "franchise@example.com", "franchisepass123")["body"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    franchise_response = client.get("/api/v1/franchise/orders", headers=headers)
    production_response = client.get("/api/v1/production/queue", headers=headers)

    assert franchise_response.status_code == 200
    assert production_response.status_code == 403


def test_production_can_access_production_route_but_not_franchise_route(client: TestClient) -> None:
    token = login(client, "production@example.com", "productionpass123")["body"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    production_response = client.get("/api/v1/production/queue", headers=headers)
    franchise_response = client.get("/api/v1/franchise/orders", headers=headers)

    assert production_response.status_code == 200
    assert franchise_response.status_code == 403


def test_client_can_create_and_list_own_orders_from_user_flow_routes(client: TestClient) -> None:
    token = login(client, "client@example.com", "clientpass123")["body"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    create_response = client.post(
        "/api/v1/client/orders",
        headers=headers,
        json={"product_id": 1, "branch_id": 1, "quantity": 2},
    )
    list_response = client.get("/api/v1/client/orders", headers=headers)

    assert create_response.status_code == 201
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1
    assert list_response.json()[0]["quantity"] == 2


def test_client_can_create_order_without_branch_id_and_server_assigns_branch(client: TestClient) -> None:
    token = login(client, "client@example.com", "clientpass123")["body"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    create_response = client.post(
        "/api/v1/client/orders",
        headers=headers,
        json={"product_id": 1, "quantity": 2, "delivery_city": "Astana"},
    )

    assert create_response.status_code == 201
    assert create_response.json()["branch_id"] == 2
    assert create_response.json()["current_deadline_stage"] == "branch_review"
    assert create_response.json()["branch_attempt_count"] == 1


def test_shared_status_endpoint_allows_real_role_transitions(client: TestClient) -> None:
    client_token = login(client, "client@example.com", "clientpass123")["body"]["access_token"]
    franchise_token = login(client, "franchise@example.com", "franchisepass123")["body"]["access_token"]
    production_token = login(client, "production@example.com", "productionpass123")["body"]["access_token"]

    create_response = client.post(
        "/api/v1/client/orders",
        headers={"Authorization": f"Bearer {client_token}"},
        json={"product_id": 1, "branch_id": 1, "quantity": 1},
    )
    order_id = create_response.json()["id"]

    accepted = client.patch(
        f"/api/v1/orders/{order_id}/status",
        headers={"Authorization": f"Bearer {franchise_token}"},
        json={"status": "accepted"},
    )
    in_production = client.patch(
        f"/api/v1/orders/{order_id}/status",
        headers={"Authorization": f"Bearer {production_token}"},
        json={"status": "in_production"},
    )
    ready = client.patch(
        f"/api/v1/orders/{order_id}/status",
        headers={"Authorization": f"Bearer {production_token}"},
        json={"status": "ready"},
    )

    assert accepted.status_code == 200
    assert in_production.status_code == 200
    assert ready.status_code == 200
    assert ready.json()["status"] == "ready"


def test_shared_status_endpoint_rejects_wrong_role_and_invalid_transition(client: TestClient) -> None:
    client_token = login(client, "client@example.com", "clientpass123")["body"]["access_token"]
    franchise_token = login(client, "franchise@example.com", "franchisepass123")["body"]["access_token"]

    create_response = client.post(
        "/api/v1/client/orders",
        headers={"Authorization": f"Bearer {client_token}"},
        json={"product_id": 1, "branch_id": 1, "quantity": 1},
    )
    order_id = create_response.json()["id"]

    wrong_role = client.patch(
        f"/api/v1/orders/{order_id}/status",
        headers={"Authorization": f"Bearer {client_token}"},
        json={"status": "accepted"},
    )
    invalid_transition = client.patch(
        f"/api/v1/orders/{order_id}/status",
        headers={"Authorization": f"Bearer {franchise_token}"},
        json={"status": "ready"},
    )

    assert wrong_role.status_code == 403
    assert invalid_transition.status_code == 400


def test_franchise_reject_endpoint_requires_note_and_reassigns_order(client: TestClient) -> None:
    client_token = login(client, "client@example.com", "clientpass123")["body"]["access_token"]
    franchise_token = login(client, "franchise@example.com", "franchisepass123")["body"]["access_token"]

    create_response = client.post(
        "/api/v1/client/orders",
        headers={"Authorization": f"Bearer {client_token}"},
        json={"product_id": 1, "branch_id": 1, "quantity": 1},
    )
    order_id = create_response.json()["id"]

    bad_reject = client.post(
        f"/api/v1/franchise/orders/{order_id}/reject",
        headers={"Authorization": f"Bearer {franchise_token}"},
        json={"note": ""},
    )
    good_reject = client.post(
        f"/api/v1/franchise/orders/{order_id}/reject",
        headers={"Authorization": f"Bearer {franchise_token}"},
        json={"note": "Cannot fulfill"},
    )

    assert bad_reject.status_code == 400
    assert good_reject.status_code == 200
    assert good_reject.json()["branch_id"] == 2
    assert good_reject.json()["status"] == "created"


def test_cancel_endpoint_enforces_state_and_role_rules(client: TestClient) -> None:
    client_token = login(client, "client@example.com", "clientpass123")["body"]["access_token"]
    franchise_token = login(client, "franchise@example.com", "franchisepass123")["body"]["access_token"]
    production_token = login(client, "production@example.com", "productionpass123")["body"]["access_token"]

    create_response = client.post(
        "/api/v1/client/orders",
        headers={"Authorization": f"Bearer {client_token}"},
        json={"product_id": 1, "branch_id": 1, "quantity": 1},
    )
    order_id = create_response.json()["id"]

    client_cancel = client.post(
        f"/api/v1/orders/{order_id}/cancel",
        headers={"Authorization": f"Bearer {client_token}"},
        json={"reason": "Client requested cancellation"},
    )

    second_order = client.post(
        "/api/v1/client/orders",
        headers={"Authorization": f"Bearer {client_token}"},
        json={"product_id": 1, "branch_id": 1, "quantity": 1},
    )
    second_order_id = second_order.json()["id"]
    client.patch(
        f"/api/v1/orders/{second_order_id}/status",
        headers={"Authorization": f"Bearer {franchise_token}"},
        json={"status": "accepted"},
    )
    client.patch(
        f"/api/v1/orders/{second_order_id}/status",
        headers={"Authorization": f"Bearer {production_token}"},
        json={"status": "in_production"},
    )
    late_client_cancel = client.post(
        f"/api/v1/orders/{second_order_id}/cancel",
        headers={"Authorization": f"Bearer {client_token}"},
        json={"reason": "Too late"},
    )
    production_cancel = client.post(
        f"/api/v1/orders/{second_order_id}/cancel",
        headers={"Authorization": f"Bearer {production_token}"},
        json={"reason": "Production stopped"},
    )

    assert client_cancel.status_code == 200
    assert client_cancel.json()["status"] == "cancelled"
    assert late_client_cancel.status_code == 403
    assert production_cancel.status_code == 200
    assert production_cancel.json()["status"] == "cancelled"


def test_production_queue_includes_escalated_orders(client: TestClient) -> None:
    from app.core.database import SessionLocal
    from app.schemas.order import UserContext
    from app.services.order_service import OrderService

    client_token = login(client, "client@example.com", "clientpass123")["body"]["access_token"]
    production_token = login(client, "production@example.com", "productionpass123")["body"]["access_token"]

    create_response = client.post(
        "/api/v1/client/orders",
        headers={"Authorization": f"Bearer {client_token}"},
        json={"product_id": 1, "branch_id": 1, "quantity": 1},
    )

    with SessionLocal() as session:
        service = OrderService(session)
        service.escalate_order(
            create_response.json()["id"],
            reason="Manual escalation for test",
            current_user=UserContext(id=3, role=UserRole.PRODUCTION, branch_id=None),
        )

    queue_response = client.get(
        "/api/v1/production/queue",
        headers={"Authorization": f"Bearer {production_token}"},
    )

    assert queue_response.status_code == 200
    assert "escalated" in {order["status"] for order in queue_response.json()}


def test_malformed_or_expired_token_returns_401(client: TestClient) -> None:
    from app.core.security import create_access_token

    expired_token = create_access_token(
        subject="1",
        role=UserRole.CLIENT,
        expires_delta=timedelta(minutes=-1),
    )

    malformed = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer not-a-jwt"},
    )
    expired = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {expired_token}"},
    )

    assert malformed.status_code == 401
    assert expired.status_code == 401
