from fastapi.testclient import TestClient


def test_products_route_exposes_localized_product_fields() -> None:
    from app.core.database import initialize_database, seed_demo_catalog, seed_demo_users
    from app.main import create_app

    initialize_database(reset=True)
    seed_demo_users()
    seed_demo_catalog()

    with TestClient(create_app()) as client:
        response = client.get("/api/v1/products")

    assert response.status_code == 200
    body = response.json()
    assert body
    first_product = body[0]
    assert "description" in first_product
    assert "display_category" in first_product
    assert "normalized_category" in first_product
    assert "season_tags" in first_product
    assert "color" in first_product
    assert "is_available" in first_product
    assert "category" not in first_product
    assert first_product["name"] == "Шелковый топ"
    assert first_product["display_category"] == "База"


def test_products_route_localizes_from_accept_language_header() -> None:
    from app.core.database import initialize_database, seed_demo_catalog, seed_demo_users
    from app.main import create_app

    initialize_database(reset=True)
    seed_demo_users()
    seed_demo_catalog()

    with TestClient(create_app()) as client:
        response = client.get("/api/v1/products", headers={"Accept-Language": "kk-KZ,ru;q=0.8"})

    assert response.status_code == 200
    first_product = response.json()[0]
    assert first_product["name"] == "Жібек топ"
    assert first_product["display_category"] == "Негізгі киім"
    assert first_product["description"] == "Жеңіл жібек топ жұмсақ жылтырмен."


def test_capsule_wardrobe_endpoint_rejects_invalid_filters() -> None:
    from app.core.database import initialize_database, seed_demo_catalog, seed_demo_users
    from app.main import create_app

    initialize_database(reset=True)
    seed_demo_users()
    seed_demo_catalog()

    with TestClient(create_app()) as client:
        invalid_categories = client.post(
            "/api/v1/wardrobes/capsule",
            json={"season": "Лето", "allowed_categories": ["dress"]},
        )
        invalid_limits = client.post(
            "/api/v1/wardrobes/capsule",
            json={"season": "Лето", "max_outfits": 9, "target_item_limit": 2},
        )

    assert invalid_categories.status_code == 422
    assert invalid_limits.status_code == 422


def test_capsule_wardrobe_endpoint_generates_outfits_from_request_catalog_override() -> None:
    from app.core.database import initialize_database, seed_demo_catalog, seed_demo_users
    from app.main import create_app

    initialize_database(reset=True)
    seed_demo_users()
    seed_demo_catalog()

    payload = {
        "season": "Лето",
        "max_outfits": 3,
        "target_item_limit": 5,
        "catalog": [
            {
                "id": 101,
                "sku": "TOP-101",
                "name": "Silk Tank",
                "display_category": "Basics",
                "season_tags": ["Лето"],
                "color": "white",
                "is_available": True,
                "is_active": True,
            },
            {
                "id": 102,
                "sku": "BOT-102",
                "name": "Tailored Trousers",
                "display_category": "Trousers",
                "season_tags": ["Лето"],
                "color": "beige",
                "is_available": True,
                "is_active": True,
            },
            {
                "id": 103,
                "sku": "OUT-103",
                "name": "Light Trench",
                "display_category": "Outerwear",
                "season_tags": ["Лето", "Весна"],
                "color": "gray",
                "is_available": True,
                "is_active": True,
            },
        ],
    }

    with TestClient(create_app()) as client:
        response = client.post("/api/v1/wardrobes/capsule", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert len(body["capsule_items"]) == 3
    assert body["outfits"]
    assert body["outfits"][0]["explanation"]
    assert set(body["outfits"][0]["colors"]).issubset({"white", "beige", "gray"})


def test_products_route_falls_back_to_default_language_when_translation_is_missing() -> None:
    from app.core.database import SessionLocal, initialize_database, seed_demo_catalog, seed_demo_users
    from app.main import create_app
    from app.models.product_translation import ProductTranslation

    initialize_database(reset=True)
    seed_demo_users()
    seed_demo_catalog()

    with TestClient(create_app()) as client:
        with SessionLocal() as session:
            translation = session.get(ProductTranslation, {"product_id": 1, "language_code": "en"})
            session.delete(translation)
            session.commit()
        response = client.get("/api/v1/products", headers={"Accept-Language": "en-US,en;q=0.8"})

    assert response.status_code == 200
    first_product = response.json()[0]
    assert first_product["name"] == "Шелковый топ"
    assert first_product["display_category"] == "База"
