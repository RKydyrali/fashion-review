from fastapi.testclient import TestClient

PNG_BYTES = b"\x89PNG\r\n\x1a\n" + (b"0" * 64)
JPEG_BYTES = b"\xff\xd8\xff" + (b"1" * 64)


def login_token(client: TestClient, username: str, password: str) -> str:
    response = client.post(
        "/api/v1/auth/login",
        data={"username": username, "password": password},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_try_on_session_create_and_idempotent_reuse() -> None:
    from app.core.database import initialize_database, seed_demo_catalog, seed_demo_size_charts, seed_demo_users
    from app.main import create_app

    initialize_database(reset=True)
    seed_demo_users()
    seed_demo_catalog()
    seed_demo_size_charts()

    with TestClient(create_app()) as client:
        token = login_token(client, "client@example.com", "clientpass123")
        data = {"product_ids": ["1", "2"]}
        files = {"user_image": ("person.png", PNG_BYTES, "image/png")}

        first = client.post(
            "/api/v1/try-on/sessions",
            headers=auth_headers(token),
            data=data,
            files=files,
        )
        second = client.post(
            "/api/v1/try-on/sessions",
            headers=auth_headers(token),
            data=data,
            files={"user_image": ("person.png", PNG_BYTES, "image/png")},
        )

    assert first.status_code == 201
    assert second.status_code == 200
    assert first.json()["id"] == second.json()["id"]
    assert first.json()["status"] == "queued"
    assert first.json()["product_ids"] == [1, 2]
    assert first.json()["source_image_url"].startswith("/media/try_on/")


def test_try_on_session_rejects_invalid_uploads() -> None:
    from app.core.database import initialize_database, seed_demo_catalog, seed_demo_users
    from app.main import create_app

    initialize_database(reset=True)
    seed_demo_users()
    seed_demo_catalog()

    with TestClient(create_app()) as client:
        token = login_token(client, "client@example.com", "clientpass123")
        unsupported = client.post(
            "/api/v1/try-on/sessions",
            headers=auth_headers(token),
            data={"product_ids": "1"},
            files={"user_image": ("person.gif", b"GIF89a", "image/gif")},
        )
        oversized = client.post(
            "/api/v1/try-on/sessions",
            headers=auth_headers(token),
            data={"product_ids": "1"},
            files={"user_image": ("person.png", b"x" * (10 * 1024 * 1024 + 1), "image/png")},
        )

    assert unsupported.status_code == 400
    assert oversized.status_code == 400


def test_try_on_session_owner_can_poll_status() -> None:
    from app.core.database import initialize_database, seed_demo_catalog, seed_demo_users
    from app.main import create_app

    initialize_database(reset=True)
    seed_demo_users()
    seed_demo_catalog()

    with TestClient(create_app()) as client:
        owner_token = login_token(client, "client@example.com", "clientpass123")
        other_token = login_token(client, "franchise@example.com", "franchisepass123")
        created = client.post(
            "/api/v1/try-on/sessions",
            headers=auth_headers(owner_token),
            data={"product_ids": "1"},
            files={"user_image": ("person.jpg", JPEG_BYTES, "image/jpeg")},
        )
        session_id = created.json()["id"]
        owner_response = client.get(
            f"/api/v1/try-on/sessions/{session_id}",
            headers=auth_headers(owner_token),
        )
        other_response = client.get(
            f"/api/v1/try-on/sessions/{session_id}",
            headers=auth_headers(other_token),
        )

    assert owner_response.status_code == 200
    assert owner_response.json()["id"] == session_id
    assert other_response.status_code == 403
