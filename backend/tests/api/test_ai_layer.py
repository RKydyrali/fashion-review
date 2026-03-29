from fastapi.testclient import TestClient


def login_token(client: TestClient, username: str, password: str) -> str:
    response = client.post(
        "/api/v1/auth/login",
        data={"username": username, "password": password},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_ai_routes_are_registered() -> None:
    from fastapi.routing import APIRoute

    from app.main import app

    http_paths = {
        route.path
        for route in app.routes
        if isinstance(route, APIRoute)
    }

    assert "/api/v1/ai/sizes/explanations" in http_paths
    assert "/api/v1/ai/wardrobes/explanations" in http_paths
    assert "/api/v1/ai/outfits/rerank" in http_paths
    assert "/api/v1/ai/stylist/recommendations" in http_paths
    assert "/api/v1/ai/try-on/jobs" in http_paths
    assert "/api/v1/ai/try-on/jobs/{job_id}" in http_paths


def test_ai_size_explanation_returns_deterministic_fallback_when_ai_is_disabled() -> None:
    from app.core.config import get_settings
    from app.core.database import initialize_database, seed_demo_catalog, seed_demo_size_charts, seed_demo_users
    from app.main import create_app

    initialize_database(reset=True)
    seed_demo_users()
    seed_demo_catalog()
    seed_demo_size_charts()

    settings = get_settings()
    settings.ai_enabled = False
    settings.ai_size_explanations_enabled = False

    with TestClient(create_app()) as client:
        token = login_token(client, "client@example.com", "clientpass123")
        response = client.post(
            "/api/v1/ai/sizes/explanations",
            headers=auth_headers(token),
            json={
                "chart_id": 1,
                "fit_type": "regular",
                "measurements": {
                    "chest_cm": 94.0,
                    "waist_cm": 76.0,
                    "hips_cm": 102.0,
                },
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["ai_status"] == "disabled"
    assert body["used_fallback"] is True
    assert body["provider_name"] is None
    assert body["model_name"] is None
    assert body["prompt_template_version"] == "size_explanation_v1"
    assert body["deterministic_result"]["recommended_size"] == "M"
    assert body["explanation"]


def test_ai_stylist_requires_auth() -> None:
    from app.core.database import initialize_database, seed_demo_catalog, seed_demo_size_charts, seed_demo_users
    from app.main import create_app

    initialize_database(reset=True)
    seed_demo_users()
    seed_demo_catalog()
    seed_demo_size_charts()

    with TestClient(create_app()) as client:
        response = client.post(
            "/api/v1/ai/stylist/recommendations",
            json={
                "season": "Р›РµС‚Рѕ",
                "occasion": "work",
            },
        )

    assert response.status_code == 401
