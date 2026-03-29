from fastapi.testclient import TestClient
import pytest

PNG_BYTES = b"\x89PNG\r\n\x1a\n" + (b"0" * 64)


class _RealtimeProvider:
    def generate(self, *, source_image_bytes: bytes, source_content_type: str, garment_image_urls: list[str]) -> tuple[bytes, str]:
        return (b"rendered-image", "image/png")


def login_token(client: TestClient, username: str, password: str) -> str:
    response = client.post(
        "/api/v1/auth/login",
        data={"username": username, "password": password},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def websocket_path(token: str) -> str:
    return f"/ws/updates?token={token}"


@pytest.fixture()
def client() -> TestClient:
    from app.core.database import initialize_database, seed_demo_catalog, seed_demo_size_charts, seed_demo_users
    from app.main import create_app

    initialize_database(reset=True)
    seed_demo_users()
    seed_demo_catalog()
    seed_demo_size_charts()

    with TestClient(create_app()) as test_client:
        yield test_client


def test_try_on_events_reach_session_owner(client: TestClient) -> None:
    from app.core.database import SessionLocal
    from app.services.try_on_worker_service import TryOnWorkerService

    token = login_token(client, "client@example.com", "clientpass123")

    with client.websocket_connect(websocket_path(token)) as websocket:
        created = client.post(
            "/api/v1/try-on/sessions",
            headers=auth_headers(token),
            data={"product_ids": "1"},
            files={"user_image": ("person.png", PNG_BYTES, "image/png")},
        )
        assert created.status_code == 201

        queued_event = websocket.receive_json()

        with SessionLocal() as session:
            worker = TryOnWorkerService(
                session,
                provider=_RealtimeProvider(),
                provider_timeout_seconds=1.0,
                max_attempts=3,
            )
            worker.process_next_session()

        processing_event = websocket.receive_json()
        completed_event = websocket.receive_json()

    assert queued_event["event"] == "try_on_queued"
    assert processing_event["event"] == "try_on_processing"
    assert completed_event["event"] == "try_on_completed"
