from datetime import timedelta

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from app.domain.order_status import OrderStatus
from app.domain.roles import UserRole


@pytest.fixture()
def client() -> TestClient:
    from app.core.database import SessionLocal, initialize_database, seed_demo_catalog, seed_demo_users
    from app.core.security import get_password_hash
    from app.domain.roles import UserRole
    from app.models.branch import Branch
    from app.models.user import User
    from app.main import create_app

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


def login_token(client: TestClient, username: str, password: str) -> str:
    response = client.post(
        "/api/v1/auth/login",
        data={"username": username, "password": password},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def websocket_path(token: str | None = None) -> str:
    if token is None:
        return "/ws/updates"
    return f"/ws/updates?token={token}"


def test_websocket_rejects_missing_token(client: TestClient) -> None:
    with pytest.raises(WebSocketDisconnect) as exc_info:
        with client.websocket_connect(websocket_path()):
            pass

    assert exc_info.value.code == status.WS_1008_POLICY_VIOLATION


def test_websocket_rejects_malformed_token(client: TestClient) -> None:
    with pytest.raises(WebSocketDisconnect) as exc_info:
        with client.websocket_connect(websocket_path("not-a-jwt")):
            pass

    assert exc_info.value.code == status.WS_1008_POLICY_VIOLATION


def test_websocket_rejects_expired_token(client: TestClient) -> None:
    from app.core.security import create_access_token

    expired_token = create_access_token(
        subject="1",
        role=UserRole.CLIENT,
        expires_delta=timedelta(minutes=-1),
    )

    with pytest.raises(WebSocketDisconnect) as exc_info:
        with client.websocket_connect(websocket_path(expired_token)):
            pass

    assert exc_info.value.code == status.WS_1008_POLICY_VIOLATION


def test_websocket_rejects_inactive_user(client: TestClient) -> None:
    from app.core.security import create_access_token

    inactive_token = create_access_token(subject="4", role=UserRole.CLIENT)

    with pytest.raises(WebSocketDisconnect) as exc_info:
        with client.websocket_connect(websocket_path(inactive_token)):
            pass

    assert exc_info.value.code == status.WS_1008_POLICY_VIOLATION


@pytest.mark.parametrize(
    ("username", "password"),
    [
        ("client@example.com", "clientpass123"),
        ("franchise@example.com", "franchisepass123"),
        ("production@example.com", "productionpass123"),
    ],
)
def test_websocket_accepts_active_authenticated_users(
    client: TestClient,
    username: str,
    password: str,
) -> None:
    token = login_token(client, username, password)

    with client.websocket_connect(websocket_path(token)):
        pass


def test_websocket_rejects_unauthorized_subscribe_requests(client: TestClient) -> None:
    client_token = login_token(client, "client@example.com", "clientpass123")

    with client.websocket_connect(websocket_path(client_token)) as websocket:
        websocket.send_json({"command": "subscribe", "channel": "branch:1"})
        message = websocket.receive_json()

    assert message["event"] == "error"
    assert message["payload"]["channel"] == "branch:1"


def test_websocket_acknowledges_unsubscribe_for_authorized_channel(client: TestClient) -> None:
    client_token = login_token(client, "client@example.com", "clientpass123")

    with client.websocket_connect(websocket_path(client_token)) as websocket:
        websocket.send_json({"command": "unsubscribe", "channel": "user:1"})
        message = websocket.receive_json()

    assert message["event"] == "unsubscribed"
    assert message["payload"]["channel"] == "user:1"


def test_order_created_event_reaches_client_and_branch_subscribers(client: TestClient) -> None:
    client_token = login_token(client, "client@example.com", "clientpass123")
    franchise_token = login_token(client, "franchise@example.com", "franchisepass123")

    with client.websocket_connect(websocket_path(client_token)) as client_socket:
        with client.websocket_connect(websocket_path(franchise_token)) as branch_socket:
            response = client.post(
                "/api/v1/client/orders",
                headers=auth_headers(client_token),
                json={"product_id": 1, "branch_id": 1, "quantity": 2},
            )

            assert response.status_code == 201

            client_event = client_socket.receive_json()
            branch_event = branch_socket.receive_json()

    assert client_event["event"] == "order_created"
    assert client_event["payload"]["client_id"] == 1
    assert client_event["payload"]["branch_id"] == 1
    assert client_event["payload"]["branch_attempt_count"] == 1
    assert client_event["payload"]["current_deadline_stage"] == "branch_review"
    assert set(client_event["channels"]) == {"user:1", "branch:1"}

    assert branch_event["event"] == "order_created"
    assert branch_event["payload"]["order_id"] == client_event["payload"]["order_id"]


def test_order_accept_event_reaches_client_branch_and_production_subscribers(client: TestClient) -> None:
    client_token = login_token(client, "client@example.com", "clientpass123")
    franchise_token = login_token(client, "franchise@example.com", "franchisepass123")
    production_token = login_token(client, "production@example.com", "productionpass123")

    create_response = client.post(
        "/api/v1/client/orders",
        headers=auth_headers(client_token),
        json={"product_id": 1, "branch_id": 1, "quantity": 1},
    )
    assert create_response.status_code == 201
    order_id = create_response.json()["id"]

    with client.websocket_connect(websocket_path(client_token)) as client_socket:
        with client.websocket_connect(websocket_path(franchise_token)) as branch_socket:
            with client.websocket_connect(websocket_path(production_token)) as production_socket:
                response = client.patch(
                    f"/api/v1/orders/{order_id}/status",
                    headers=auth_headers(franchise_token),
                    json={"status": "accepted"},
                )

                assert response.status_code == 200

                client_event = client_socket.receive_json()
                branch_event = branch_socket.receive_json()
                production_event = production_socket.receive_json()

    for event in (client_event, branch_event, production_event):
        assert event["event"] == "order_status_changed"
        assert event["payload"]["order_id"] == order_id
        assert event["payload"]["status"] == OrderStatus.ACCEPTED.value
        assert event["payload"]["previous_status"] == OrderStatus.CREATED.value

    assert set(production_event["channels"]) == {"user:1", "branch:1", "role:production"}


def test_production_progress_events_reach_branch_and_production_subscribers(client: TestClient) -> None:
    client_token = login_token(client, "client@example.com", "clientpass123")
    franchise_token = login_token(client, "franchise@example.com", "franchisepass123")
    production_token = login_token(client, "production@example.com", "productionpass123")

    create_response = client.post(
        "/api/v1/client/orders",
        headers=auth_headers(client_token),
        json={"product_id": 1, "branch_id": 1, "quantity": 1},
    )
    order_id = create_response.json()["id"]

    accept_response = client.patch(
        f"/api/v1/orders/{order_id}/status",
        headers=auth_headers(franchise_token),
        json={"status": "accepted"},
    )
    assert accept_response.status_code == 200

    with client.websocket_connect(websocket_path(client_token)) as client_socket:
        with client.websocket_connect(websocket_path(franchise_token)) as branch_socket:
            with client.websocket_connect(websocket_path(production_token)) as production_socket:
                start_response = client.patch(
                    f"/api/v1/orders/{order_id}/status",
                    headers=auth_headers(production_token),
                    json={"status": "in_production"},
                )
                ready_response = client.patch(
                    f"/api/v1/orders/{order_id}/status",
                    headers=auth_headers(production_token),
                    json={"status": "ready"},
                )

                assert start_response.status_code == 200
                assert ready_response.status_code == 200

                start_events = [
                    client_socket.receive_json(),
                    branch_socket.receive_json(),
                    production_socket.receive_json(),
                ]
                ready_events = [
                    client_socket.receive_json(),
                    branch_socket.receive_json(),
                    production_socket.receive_json(),
                ]

    for event in start_events:
        assert event["event"] == "order_status_changed"
        assert event["payload"]["status"] == OrderStatus.IN_PRODUCTION.value
        assert event["payload"]["previous_status"] == OrderStatus.ACCEPTED.value

    for event in ready_events:
        assert event["event"] == "order_status_changed"
        assert event["payload"]["status"] == OrderStatus.READY.value
        assert event["payload"]["previous_status"] == OrderStatus.IN_PRODUCTION.value


def test_order_reassigned_event_reaches_client_old_branch_and_new_branch(client: TestClient) -> None:
    client_token = login_token(client, "client@example.com", "clientpass123")
    franchise_token = login_token(client, "franchise@example.com", "franchisepass123")
    second_franchise_token = login_token(client, "second-franchise@example.com", "secondfranchisepass123")

    create_response = client.post(
        "/api/v1/client/orders",
        headers=auth_headers(client_token),
        json={"product_id": 1, "branch_id": 1, "quantity": 1},
    )
    assert create_response.status_code == 201
    order_id = create_response.json()["id"]

    with client.websocket_connect(websocket_path(client_token)) as client_socket:
        with client.websocket_connect(websocket_path(franchise_token)) as branch_one_socket:
            with client.websocket_connect(websocket_path(second_franchise_token)) as branch_two_socket:
                response = client.post(
                    f"/api/v1/franchise/orders/{order_id}/reject",
                    headers=auth_headers(franchise_token),
                    json={"note": "Cannot fulfill"},
                )

                assert response.status_code == 200

                client_event = client_socket.receive_json()
                old_branch_event = branch_one_socket.receive_json()
                new_branch_event = branch_two_socket.receive_json()

    for event in (client_event, old_branch_event, new_branch_event):
        assert event["event"] == "order_reassigned"
        assert event["payload"]["order_id"] == order_id
        assert event["payload"]["previous_branch_id"] == 1
        assert event["payload"]["branch_id"] == 2
        assert event["payload"]["branch_attempt_count"] == 2


def test_disconnected_socket_does_not_break_delivery_to_remaining_subscribers(client: TestClient) -> None:
    client_token = login_token(client, "client@example.com", "clientpass123")
    franchise_token = login_token(client, "franchise@example.com", "franchisepass123")

    with client.websocket_connect(websocket_path(franchise_token)):
        pass

    with client.websocket_connect(websocket_path(franchise_token)) as remaining_socket:
        response = client.post(
            "/api/v1/client/orders",
            headers=auth_headers(client_token),
            json={"product_id": 1, "branch_id": 1, "quantity": 4},
        )

        assert response.status_code == 201
        event = remaining_socket.receive_json()

    assert event["event"] == "order_created"
    assert event["payload"]["quantity"] == 4
