def test_catalog_service_localizes_requested_language() -> None:
    from app.core.database import SessionLocal, initialize_database, seed_demo_catalog
    from app.domain.language import LanguageCode
    from app.services.catalog_service import CatalogService

    initialize_database(reset=True)
    seed_demo_catalog()

    with SessionLocal() as session:
        service = CatalogService(session)
        products = service.list_products(LanguageCode.EN)

    assert products
    assert products[0].name == "Silk Shell Top"
    assert products[0].display_category == "Basics"
    assert products[0].description == "Lightweight silk top with a soft sheen."


def test_catalog_service_falls_back_to_russian_when_requested_translation_is_missing() -> None:
    from app.core.database import SessionLocal, initialize_database, seed_demo_catalog
    from app.domain.language import LanguageCode
    from app.models.product_translation import ProductTranslation
    from app.services.catalog_service import CatalogService

    initialize_database(reset=True)
    seed_demo_catalog()

    with SessionLocal() as session:
        translation = session.get(ProductTranslation, {"product_id": 1, "language_code": LanguageCode.KK})
        session.delete(translation)
        session.commit()

        service = CatalogService(session)
        products = service.list_products(LanguageCode.KK)

    assert products
    assert products[0].name == "Шелковый топ"
    assert products[0].display_category == "База"
    assert products[0].description == "Легкий шелковый топ с мягким блеском."
