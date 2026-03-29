from fastapi.testclient import TestClient


def login_token(client: TestClient, username: str, password: str) -> str:
    response = client.post(
        "/api/v1/auth/login",
        data={"username": username, "password": password},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def test_size_recommendation_endpoint_accepts_stored_chart_lookup() -> None:
    from app.core.database import (
        initialize_database,
        seed_demo_catalog,
        seed_demo_size_charts,
        seed_demo_users,
    )
    from app.main import create_app

    initialize_database(reset=True)
    seed_demo_users()
    seed_demo_catalog()
    seed_demo_size_charts()

    payload = {
        "chart_id": 1,
        "fit_type": "regular",
        "measurements": {
            "chest_cm": 94.0,
            "waist_cm": 76.0,
            "hips_cm": 102.0,
        },
    }

    with TestClient(create_app()) as client:
        response = client.post("/api/v1/sizes/recommend", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["recommended_size"] == "M"
    assert body["base_size"] == "M"
    assert body["confidence"] == "high"
    assert body["confidence_score"] == 0.0
    assert body["match_method"] == "exact_range"
    assert body["warnings"] == []


def test_size_recommendation_endpoint_rejects_invalid_chart_source_combinations() -> None:
    from app.core.database import initialize_database, seed_demo_catalog, seed_demo_users
    from app.main import create_app

    initialize_database(reset=True)
    seed_demo_users()
    seed_demo_catalog()

    inline_chart = {
        "name": "Inline Tops",
        "sizes": [
            {
                "size_label": "S",
                "chest_min_cm": 84,
                "chest_max_cm": 90,
                "waist_min_cm": 66,
                "waist_max_cm": 72,
                "hips_min_cm": 92,
                "hips_max_cm": 98,
            }
        ],
    }

    with TestClient(create_app()) as client:
        missing_source = client.post(
            "/api/v1/sizes/recommend",
            json={
                "fit_type": "regular",
                "measurements": {"chest_cm": 88, "waist_cm": 70, "hips_cm": 95},
            },
        )
        duplicate_source = client.post(
            "/api/v1/sizes/recommend",
            json={
                "chart_id": 1,
                "size_chart": inline_chart,
                "fit_type": "regular",
                "measurements": {"chest_cm": 88, "waist_cm": 70, "hips_cm": 95},
            },
        )

    assert missing_source.status_code == 422
    assert duplicate_source.status_code == 422


def test_size_recommendation_uses_saved_measurements_for_authenticated_user_when_request_omits_them() -> None:
    from app.core.database import SessionLocal, initialize_database, seed_demo_catalog, seed_demo_size_charts, seed_demo_users
    from app.main import create_app
    from app.models.user import User

    initialize_database(reset=True)
    seed_demo_users()
    seed_demo_catalog()
    seed_demo_size_charts()

    with SessionLocal() as session:
        user = session.get(User, 1)
        assert user is not None
        user.chest_cm = 94.0
        user.waist_cm = 76.0
        user.hips_cm = 102.0
        session.commit()

    with TestClient(create_app()) as client:
        token = login_token(client, "client@example.com", "clientpass123")
        response = client.post(
            "/api/v1/sizes/recommend",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "chart_id": 1,
                "fit_type": "regular",
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["recommended_size"] == "M"
    assert body["base_size"] == "M"


def test_size_recommendation_prefers_explicit_measurements_over_saved_profile_values() -> None:
    from app.core.database import SessionLocal, initialize_database, seed_demo_catalog, seed_demo_size_charts, seed_demo_users
    from app.main import create_app
    from app.models.user import User

    initialize_database(reset=True)
    seed_demo_users()
    seed_demo_catalog()
    seed_demo_size_charts()

    with SessionLocal() as session:
        user = session.get(User, 1)
        assert user is not None
        user.chest_cm = 88.0
        user.waist_cm = 70.0
        user.hips_cm = 97.0
        session.commit()

    with TestClient(create_app()) as client:
        token = login_token(client, "client@example.com", "clientpass123")
        response = client.post(
            "/api/v1/sizes/recommend",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "chart_id": 1,
                "fit_type": "regular",
                "measurements": {
                    "chest_cm": 100.0,
                    "waist_cm": 83.0,
                    "hips_cm": 109.0,
                },
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["recommended_size"] == "L"
    assert body["base_size"] == "L"


def test_size_recommendation_rejects_missing_measurements_when_saved_profile_is_incomplete() -> None:
    from app.core.database import SessionLocal, initialize_database, seed_demo_catalog, seed_demo_size_charts, seed_demo_users
    from app.main import create_app
    from app.models.user import User

    initialize_database(reset=True)
    seed_demo_users()
    seed_demo_catalog()
    seed_demo_size_charts()

    with SessionLocal() as session:
        user = session.get(User, 1)
        assert user is not None
        user.chest_cm = 94.0
        user.waist_cm = None
        user.hips_cm = 102.0
        session.commit()

    with TestClient(create_app()) as client:
        token = login_token(client, "client@example.com", "clientpass123")
        response = client.post(
            "/api/v1/sizes/recommend",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "chart_id": 1,
                "fit_type": "regular",
            },
        )

    assert response.status_code == 422


def test_size_recommendation_rejects_missing_measurements_for_unauthenticated_request() -> None:
    from app.core.database import initialize_database, seed_demo_catalog, seed_demo_size_charts, seed_demo_users
    from app.main import create_app

    initialize_database(reset=True)
    seed_demo_users()
    seed_demo_catalog()
    seed_demo_size_charts()

    with TestClient(create_app()) as client:
        response = client.post(
            "/api/v1/sizes/recommend",
            json={
                "chart_id": 1,
                "fit_type": "regular",
            },
        )

    assert response.status_code == 422
