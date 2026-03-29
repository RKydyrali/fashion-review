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


def test_signup_refresh_and_logout_manage_consumer_session_lifecycle() -> None:
    from app.core.database import initialize_database, seed_demo_catalog, seed_demo_size_charts, seed_demo_users
    from app.main import create_app

    initialize_database(reset=True)
    seed_demo_users()
    seed_demo_catalog()
    seed_demo_size_charts()

    with TestClient(create_app()) as client:
        signup = client.post(
            "/api/v1/auth/signup",
            json={
                "email": "newclient@example.com",
                "full_name": "New Client",
                "password": "newclientpass123",
                "preferred_language": "en",
            },
        )
        assert signup.status_code == 201
        signup_body = signup.json()
        assert signup_body["user"]["email"] == "newclient@example.com"
        assert signup_body["refresh_token"]

        refreshed = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": signup_body["refresh_token"]},
        )
        assert refreshed.status_code == 200
        refreshed_body = refreshed.json()
        assert refreshed_body["access_token"]
        assert refreshed_body["refresh_token"] != signup_body["refresh_token"]

        logged_out = client.post(
            "/api/v1/auth/logout",
            json={"refresh_token": refreshed_body["refresh_token"]},
        )
        assert logged_out.status_code == 204

        rejected_refresh = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refreshed_body["refresh_token"]},
        )
        assert rejected_refresh.status_code == 401


def test_editorial_feed_product_detail_and_size_chart_match_mobile_contract() -> None:
    from app.core.database import initialize_database, seed_demo_catalog, seed_demo_size_charts, seed_demo_users
    from app.main import create_app

    initialize_database(reset=True)
    seed_demo_users()
    seed_demo_catalog()
    seed_demo_size_charts()

    with TestClient(create_app()) as client:
        feed = client.get("/api/v1/feed", headers={"Accept-Language": "en-US,en;q=0.9"})
        collections = client.get("/api/v1/collections", headers={"Accept-Language": "en-US,en;q=0.9"})
        product = client.get("/api/v1/products/silk-shell-top", headers={"Accept-Language": "en-US,en;q=0.9"})
        size_chart = client.get("/api/v1/size-charts/1")

    assert feed.status_code == 200
    assert feed.json()["hero"]["title"]
    assert feed.json()["sections"]

    assert collections.status_code == 200
    assert collections.json()
    assert collections.json()[0]["slug"]

    assert product.status_code == 200
    product_body = product.json()
    assert product_body["slug"] == "silk-shell-top"
    assert product_body["name"] == "Silk Shell Top"
    assert product_body["price_breakdown"]["base_price"]["amount_minor"] > 0
    assert product_body["size_chart_id"] == 1
    assert any(option["size_label"] == "4XL" for option in product_body["size_options"])
    extended_option = next(
        option for option in product_body["size_options"] if option["size_label"] == "4XL"
    )
    assert extended_option["price_breakdown"]["tailoring_adjustment"]["amount_minor"] > 0
    assert extended_option["price_breakdown"]["adjustment_label"] == "Extended size tailoring"

    assert size_chart.status_code == 200
    chart_body = size_chart.json()
    assert chart_body["name"] == "AVISHU Signature Size Guide"
    assert chart_body["sizes"][0]["size_label"] == "XS"
    assert chart_body["sizes"][-1]["size_label"] == "6XL"


def test_client_can_manage_favorites_bag_and_preorder_submission_from_mobile_flow() -> None:
    from app.core.database import initialize_database, seed_demo_catalog, seed_demo_size_charts, seed_demo_users
    from app.main import create_app

    initialize_database(reset=True)
    seed_demo_users()
    seed_demo_catalog()
    seed_demo_size_charts()

    with TestClient(create_app()) as client:
        token = login_token(client, "client@example.com", "clientpass123")
        headers = auth_headers(token)

        favorite = client.post(
            "/api/v1/client/favorites",
            headers=headers,
            json={"product_id": 1},
        )
        favorites = client.get("/api/v1/client/favorites", headers=headers)
        bag_item = client.post(
            "/api/v1/client/bag/items",
            headers=headers,
            json={"product_id": 1, "size_label": "4XL", "quantity": 2},
        )

        assert favorite.status_code == 201
        assert favorites.status_code == 200
        assert favorites.json()[0]["product"]["slug"] == "silk-shell-top"

        assert bag_item.status_code == 201
        bag_body = bag_item.json()
        assert bag_body["price_breakdown"]["tailoring_adjustment"]["amount_minor"] > 0
        assert bag_body["line_total"]["amount_minor"] == (
            bag_body["price_breakdown"]["total_price"]["amount_minor"] * 2
        )

        updated = client.patch(
            f"/api/v1/client/bag/items/{bag_body['id']}",
            headers=headers,
            json={"size_label": "M", "quantity": 1},
        )
        assert updated.status_code == 200
        assert updated.json()["price_breakdown"]["tailoring_adjustment"]["amount_minor"] == 0

        second_bag_item = client.post(
            "/api/v1/client/bag/items",
            headers=headers,
            json={"product_id": 3, "size_label": "5XL", "quantity": 1},
        )
        assert second_bag_item.status_code == 201

        submitted = client.post(
            "/api/v1/client/preorders/submit",
            headers=headers,
            json={"delivery_city": "Astana"},
        )
        assert submitted.status_code == 201
        submitted_body = submitted.json()
        assert submitted_body["item_count"] == 2
        assert len(submitted_body["orders"]) == 2
        assert all(order["preorder_batch_id"] == submitted_body["id"] for order in submitted_body["orders"])

        bag_after_submit = client.get("/api/v1/client/bag/items", headers=headers)
        orders = client.get("/api/v1/client/orders", headers=headers)
        preorders = client.get("/api/v1/client/preorders", headers=headers)

    assert bag_after_submit.status_code == 200
    assert bag_after_submit.json()["items"] == []

    assert orders.status_code == 200
    assert len(orders.json()) == 2
    assert {order["size_label"] for order in orders.json()} == {"M", "5XL"}

    assert preorders.status_code == 200
    assert preorders.json()[0]["id"] == submitted_body["id"]


def test_client_can_submit_only_selected_bag_items_and_keep_the_rest() -> None:
    from app.core.database import initialize_database, seed_demo_catalog, seed_demo_size_charts, seed_demo_users
    from app.main import create_app

    initialize_database(reset=True)
    seed_demo_users()
    seed_demo_catalog()
    seed_demo_size_charts()

    with TestClient(create_app()) as client:
        token = login_token(client, "client@example.com", "clientpass123")
        headers = auth_headers(token)

        first_item = client.post(
            "/api/v1/client/bag/items",
            headers=headers,
            json={"product_id": 1, "size_label": "M", "quantity": 1},
        )
        second_item = client.post(
            "/api/v1/client/bag/items",
            headers=headers,
            json={"product_id": 3, "size_label": "5XL", "quantity": 2},
        )

        assert first_item.status_code == 201
        assert second_item.status_code == 201

        first_item_body = first_item.json()
        second_item_body = second_item.json()

        submitted = client.post(
            "/api/v1/client/preorders/submit-selected",
            headers=headers,
            json={
                "delivery_city": "Astana",
                "bag_item_ids": [second_item_body["id"]],
            },
        )
        assert submitted.status_code == 201
        submitted_body = submitted.json()
        assert submitted_body["item_count"] == 1
        assert len(submitted_body["orders"]) == 1
        assert submitted_body["orders"][0]["product_id"] == second_item_body["product"]["id"]
        assert submitted_body["orders"][0]["quantity"] == 2

        bag_after_submit = client.get("/api/v1/client/bag/items", headers=headers)
        orders = client.get("/api/v1/client/orders", headers=headers)

    assert bag_after_submit.status_code == 200
    remaining_ids = [item["id"] for item in bag_after_submit.json()["items"]]
    assert remaining_ids == [first_item_body["id"]]

    assert orders.status_code == 200
    orders_body = orders.json()
    assert len(orders_body) == 1
    assert orders_body[0]["product_id"] == second_item_body["product"]["id"]
