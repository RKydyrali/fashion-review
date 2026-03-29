def test_seeded_products_preserve_display_category_and_normalize_for_wardrobe_use() -> None:
    from app.core.database import SessionLocal, initialize_database, seed_demo_catalog
    from app.repositories.product_repository import ProductRepository

    initialize_database(reset=True)
    seed_demo_catalog()

    with SessionLocal() as session:
        repository = ProductRepository(session)
        products = repository.list_all()

    assert products
    assert all(product.display_category for product in products)
    assert all(product.normalized_category in {"top", "bottom", "outerwear"} for product in products)
    assert any(product.display_category == "Верхняя одежда" for product in products)
    assert all(product.season_tags for product in products)


def test_product_fixture_contains_valid_unicode_translations_for_all_supported_languages() -> None:
    from app.seed.seed_data import load_fixture

    products = load_fixture("products")

    assert products
    assert any(product["display_category"] == "Верхняя одежда" for product in products)
    assert all(
        {translation["language_code"] for translation in product["translations"]} == {"ru", "kk", "en"}
        for product in products
    )
