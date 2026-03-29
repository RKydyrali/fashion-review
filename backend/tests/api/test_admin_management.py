from io import BytesIO

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


def image_upload(name: str = "image.png") -> dict[str, tuple[str, BytesIO, str]]:
    return {"file": (name, BytesIO(b"fake-image-bytes"), "image/png")}


def test_admin_login_and_route_access_control() -> None:
    from app.core.database import initialize_database, seed_demo_catalog, seed_demo_size_charts, seed_demo_users
    from app.main import create_app

    initialize_database(reset=True)
    seed_demo_users()
    seed_demo_catalog()
    seed_demo_size_charts()

    with TestClient(create_app()) as client:
        admin_login = client.post(
            "/api/v1/auth/login",
            data={"username": "admin@gmail.com", "password": "admin"},
        )
        assert admin_login.status_code == 200
        assert admin_login.json()["user"]["role"] == "admin"

        admin_headers = auth_headers(admin_login.json()["access_token"])
        user_headers = auth_headers(login_token(client, "client@example.com", "clientpass123"))

        admin_users = client.get("/api/v1/admin/users", headers=admin_headers)
        denied_users = client.get("/api/v1/admin/users", headers=user_headers)
        branches = client.get("/api/v1/admin/branches", headers=admin_headers)

    assert admin_users.status_code == 200
    assert any(user["email"] == "admin@gmail.com" for user in admin_users.json())
    assert denied_users.status_code == 403
    assert branches.status_code == 200
    assert branches.json()


def test_admin_can_create_update_and_downgrade_staff_accounts() -> None:
    from app.core.database import SessionLocal, initialize_database, seed_demo_catalog, seed_demo_size_charts, seed_demo_users
    from app.main import create_app
    from app.models.branch import Branch

    initialize_database(reset=True)
    seed_demo_users()
    seed_demo_catalog()
    seed_demo_size_charts()

    with TestClient(create_app()) as client:
        admin_headers = auth_headers(login_token(client, "admin@gmail.com", "admin"))

        created = client.post(
            "/api/v1/admin/users",
            headers=admin_headers,
            json={
                "email": "newfranchise@example.com",
                "full_name": "New Franchise",
                "password": "franchisepass123",
                "role": "franchisee",
                "branch_id": 1,
            },
        )
        assert created.status_code == 201
        created_body = created.json()
        assert created_body["role"] == "franchisee"
        assert created_body["branch_id"] == 1

        updated = client.patch(
            f"/api/v1/admin/users/{created_body['id']}",
            headers=admin_headers,
            json={"role": "production", "branch_id": None},
        )
        assert updated.status_code == 200
        assert updated.json()["role"] == "production"
        assert updated.json()["branch_id"] is None

        downgraded = client.patch(
            f"/api/v1/admin/users/{created_body['id']}",
            headers=admin_headers,
            json={"role": "client"},
        )
        assert downgraded.status_code == 200
        assert downgraded.json()["role"] == "client"
        assert downgraded.json()["branch_id"] is None

        bad_create = client.post(
            "/api/v1/admin/users",
            headers=admin_headers,
            json={
                "email": "badproduction@example.com",
                "full_name": "Bad Production",
                "password": "productionpass123",
                "role": "production",
                "branch_id": 1,
            },
        )

    assert bad_create.status_code == 400

    with SessionLocal() as session:
        branch = session.get(Branch, 1)
        assert branch is not None
        assert branch.manager_user_id == 2


def test_admin_can_upload_and_manage_products_with_soft_delete() -> None:
    from app.core.database import initialize_database, seed_demo_catalog, seed_demo_size_charts, seed_demo_users
    from app.main import create_app

    initialize_database(reset=True)
    seed_demo_users()
    seed_demo_catalog()
    seed_demo_size_charts()

    with TestClient(create_app()) as client:
        admin_headers = auth_headers(login_token(client, "admin@gmail.com", "admin"))

        hero = client.post("/api/v1/admin/uploads/products/hero-image", headers=admin_headers, files=image_upload("hero.png"))
        reference = client.post(
            "/api/v1/admin/uploads/products/reference-image",
            headers=admin_headers,
            files=image_upload("reference.png"),
        )
        gallery = client.post(
            "/api/v1/admin/uploads/products/gallery-image",
            headers=admin_headers,
            files=image_upload("gallery.png"),
        )

        assert hero.status_code == 201
        assert reference.status_code == 201
        assert gallery.status_code == 201

        created = client.post(
            "/api/v1/admin/products",
            headers=admin_headers,
            json={
                "sku": "ADM-001",
                "slug": "admin-created-look",
                "normalized_category": "dress",
                "season_tags": ["spring", "editorial"],
                "color": "Ivory",
                "base_price_minor": 45500,
                "currency": "USD",
                "collection_slug": None,
                "hero_image_url": hero.json()["url"],
                "reference_image_url": reference.json()["url"],
                "gallery_image_urls": [gallery.json()["url"]],
                "available_sizes": ["S", "M", "L"],
                "size_chart_id": 1,
                "editorial_rank": 6,
                "is_featured": True,
                "is_available": True,
                "is_active": True,
                "translations": {
                    "en": {
                        "name": "Admin Created Look",
                        "description": "English description",
                        "subtitle": "English subtitle",
                        "long_description": "English long description",
                        "fabric_notes": "English fabric",
                        "care_notes": "English care",
                        "preorder_note": "English preorder",
                        "display_category": "Dresses",
                    },
                    "ru": {
                        "name": "Созданный образ",
                        "description": "Русское описание",
                        "subtitle": "Русский подзаголовок",
                        "long_description": "Русское полное описание",
                        "fabric_notes": "Русская ткань",
                        "care_notes": "Русский уход",
                        "preorder_note": "Русский предзаказ",
                        "display_category": "Платья",
                    },
                    "kk": {
                        "name": "Жаңа образ",
                        "description": "Қазақша сипаттама",
                        "subtitle": "Қазақша тақырыпша",
                        "long_description": "Қазақша толық сипаттама",
                        "fabric_notes": "Қазақша мата",
                        "care_notes": "Қазақша күтім",
                        "preorder_note": "Қазақша алдын ала тапсырыс",
                        "display_category": "Көйлектер",
                    },
                },
            },
        )
        assert created.status_code == 201
        product_id = created.json()["id"]

        updated = client.patch(
            f"/api/v1/admin/products/{product_id}",
            headers=admin_headers,
            json={"color": "Black", "is_featured": False},
        )
        assert updated.status_code == 200
        assert updated.json()["color"] == "Black"
        assert updated.json()["is_featured"] is False

        hidden = client.delete(f"/api/v1/admin/products/{product_id}", headers=admin_headers)
        public_products = client.get("/api/v1/products", headers={"Accept-Language": "en"})
        restored = client.post(f"/api/v1/admin/products/{product_id}/restore", headers=admin_headers)

    assert hidden.status_code == 200
    assert restored.status_code == 200
    assert all(product["slug"] != "admin-created-look" for product in public_products.json())


def test_admin_can_permanently_delete_product_without_order_history() -> None:
    from app.core.database import initialize_database, seed_demo_catalog, seed_demo_size_charts, seed_demo_users
    from app.main import create_app

    initialize_database(reset=True)
    seed_demo_users()
    seed_demo_catalog()
    seed_demo_size_charts()

    with TestClient(create_app()) as client:
        admin_headers = auth_headers(login_token(client, "admin@gmail.com", "admin"))

        created = client.post(
            "/api/v1/admin/products",
            headers=admin_headers,
            json={
                "sku": "ADM-DELETE-001",
                "slug": "admin-delete-look",
                "normalized_category": "dress",
                "season_tags": ["spring"],
                "color": "Ivory",
                "base_price_minor": 30000,
                "currency": "USD",
                "collection_slug": None,
                "hero_image_url": None,
                "reference_image_url": None,
                "gallery_image_urls": [],
                "available_sizes": ["S", "M"],
                "size_chart_id": 1,
                "editorial_rank": 9,
                "is_featured": False,
                "is_available": True,
                "is_active": True,
                "translations": {
                    "en": {
                        "name": "Delete Look",
                        "description": "English description",
                        "subtitle": "English subtitle",
                        "long_description": "English long description",
                        "fabric_notes": "English fabric",
                        "care_notes": "English care",
                        "preorder_note": "English preorder",
                        "display_category": "Dresses",
                    },
                    "ru": {
                        "name": "Удалить образ",
                        "description": "Русское описание",
                        "subtitle": "Русский подзаголовок",
                        "long_description": "Русское полное описание",
                        "fabric_notes": "Русская ткань",
                        "care_notes": "Русский уход",
                        "preorder_note": "Русский предзаказ",
                        "display_category": "Платья",
                    },
                    "kk": {
                        "name": "Жою образы",
                        "description": "Қазақша сипаттама",
                        "subtitle": "Қазақша тақырыпша",
                        "long_description": "Қазақша толық сипаттама",
                        "fabric_notes": "Қазақша мата",
                        "care_notes": "Қазақша күтім",
                        "preorder_note": "Қазақша алдын ала тапсырыс",
                        "display_category": "Көйлектер",
                    },
                },
            },
        )
        assert created.status_code == 201
        product_id = created.json()["id"]

        deleted = client.delete(f"/api/v1/admin/products/{product_id}/permanent", headers=admin_headers)
        products = client.get("/api/v1/admin/products", headers=admin_headers)

    assert deleted.status_code == 204
    assert all(product["id"] != product_id for product in products.json())


def test_admin_cannot_permanently_delete_product_with_order_history() -> None:
    from app.core.database import SessionLocal, initialize_database, seed_demo_catalog, seed_demo_size_charts, seed_demo_users
    from app.main import create_app
    from app.models.order import Order

    initialize_database(reset=True)
    seed_demo_users()
    seed_demo_catalog()
    seed_demo_size_charts()

    with SessionLocal() as session:
        order = Order(
            client_id=1,
            product_id=1,
            branch_id=1,
            quantity=1,
            unit_price_minor=10000,
            tailoring_adjustment_minor=0,
            total_price_minor=10000,
            currency="USD",
        )
        session.add(order)
        session.commit()

    with TestClient(create_app()) as client:
        admin_headers = auth_headers(login_token(client, "admin@gmail.com", "admin"))
        deleted = client.delete("/api/v1/admin/products/1/permanent", headers=admin_headers)

    assert deleted.status_code == 409
    assert deleted.json()["detail"] == "Products with order history cannot be deleted permanently"


def test_admin_can_generate_product_translations_from_english() -> None:
    from app.api.deps import get_ai_text_service
    from app.core.database import initialize_database, seed_demo_catalog, seed_demo_size_charts, seed_demo_users
    from app.main import create_app
    from app.schemas.ai import AIProductTranslationContent, AIProductTranslationMap, AIProductTranslationResponse

    class FakeAITextService:
        def translate_product_copy_from_english(self, *, english_copy: dict, normalized_category: str | None, color: str | None, season_tags: list[str], user_id: int | None = None) -> AIProductTranslationResponse:
            assert english_copy["name"] == "Evening Dress"
            assert normalized_category == "dress"
            assert color == "Ivory"
            assert season_tags == ["spring", "event"]
            assert user_id is not None
            return AIProductTranslationResponse(
                ai_status="completed",
                provider_name="openrouter",
                model_name="arcee-ai/trinity-large-preview:free",
                prompt_template_version="product_translation_v1",
                used_fallback=False,
                error_message=None,
                translations=AIProductTranslationMap(
                    ru=AIProductTranslationContent(
                        name="Вечернее платье",
                        description="Русское описание",
                        subtitle="Русский подзаголовок",
                        long_description="Русское полное описание",
                        fabric_notes="Русская ткань",
                        care_notes="Русский уход",
                        preorder_note="Русский предзаказ",
                        display_category="Платья",
                    ),
                    kk=AIProductTranslationContent(
                        name="Кешкі көйлек",
                        description="Қазақша сипаттама",
                        subtitle="Қазақша тақырыпша",
                        long_description="Қазақша толық сипаттама",
                        fabric_notes="Қазақша мата",
                        care_notes="Қазақша күтім",
                        preorder_note="Қазақша алдын ала тапсырыс",
                        display_category="Көйлектер",
                    ),
                ),
            )

    initialize_database(reset=True)
    seed_demo_users()
    seed_demo_catalog()
    seed_demo_size_charts()

    app = create_app()
    app.dependency_overrides[get_ai_text_service] = lambda: FakeAITextService()

    with TestClient(app) as client:
        admin_headers = auth_headers(login_token(client, "admin@gmail.com", "admin"))

        translated = client.post(
            "/api/v1/admin/products/translate",
            headers=admin_headers,
            json={
                "english": {
                    "name": "Evening Dress",
                    "description": "English description",
                    "subtitle": "English subtitle",
                    "long_description": "English long description",
                    "fabric_notes": "English fabric",
                    "care_notes": "English care",
                    "preorder_note": "English preorder",
                    "display_category": "Dresses",
                },
                "normalized_category": "dress",
                "color": "Ivory",
                "season_tags": ["spring", "event"],
            },
        )

    app.dependency_overrides.clear()

    assert translated.status_code == 200
    body = translated.json()
    assert body["ai_status"] == "completed"
    assert body["translations"]["ru"]["name"] == "Вечернее платье"
    assert body["translations"]["kk"]["display_category"] == "Көйлектер"


def test_admin_can_upload_and_manage_collections_and_unassign_products_on_archive() -> None:
    from app.core.database import initialize_database, seed_demo_catalog, seed_demo_size_charts, seed_demo_users
    from app.main import create_app

    initialize_database(reset=True)
    seed_demo_users()
    seed_demo_catalog()
    seed_demo_size_charts()

    with TestClient(create_app()) as client:
        admin_headers = auth_headers(login_token(client, "admin@gmail.com", "admin"))

        hero = client.post("/api/v1/admin/uploads/collections/hero-image", headers=admin_headers, files=image_upload("hero.png"))
        cover = client.post(
            "/api/v1/admin/uploads/collections/cover-image",
            headers=admin_headers,
            files=image_upload("cover.png"),
        )

        assert hero.status_code == 201
        assert cover.status_code == 201

        created = client.post(
            "/api/v1/admin/collections",
            headers=admin_headers,
            json={
                "slug": "admin-curation",
                "hero_image_url": hero.json()["url"],
                "cover_image_url": cover.json()["url"],
                "sort_order": 10,
                "is_featured": True,
                "is_active": True,
                "translations": {
                    "en": {"title": "Admin Curation", "summary": "English summary", "eyebrow": "Admin"},
                    "ru": {"title": "Кураторский выбор", "summary": "Русское summary", "eyebrow": "Админ"},
                    "kk": {"title": "Әкім таңдауы", "summary": "Қазақша summary", "eyebrow": "Әкім"},
                },
            },
        )
        assert created.status_code == 201
        collection_id = created.json()["id"]

        reassigned_product = client.patch(
            "/api/v1/admin/products/1",
            headers=admin_headers,
            json={"collection_slug": "admin-curation"},
        )
        assert reassigned_product.status_code == 200
        assert reassigned_product.json()["collection_slug"] == "admin-curation"

        hidden = client.delete(f"/api/v1/admin/collections/{collection_id}", headers=admin_headers)
        public_collections = client.get("/api/v1/collections", headers={"Accept-Language": "en"})
        product_detail = client.get("/api/v1/products/silk-shell-top", headers={"Accept-Language": "en"})
        restored = client.post(f"/api/v1/admin/collections/{collection_id}/restore", headers=admin_headers)

    assert hidden.status_code == 200
    assert restored.status_code == 200
    assert all(collection["slug"] != "admin-curation" for collection in public_collections.json())
    assert product_detail.status_code == 200
    assert product_detail.json()["collection_slug"] is None
