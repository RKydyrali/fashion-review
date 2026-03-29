def test_capsule_service_prefers_neutral_reusable_items_and_respects_limits() -> None:
    from app.schemas.wardrobe import CapsuleWardrobeRequest, WardrobeCatalogItemInput
    from app.services.wardrobe_service import WardrobeService

    service = WardrobeService()
    result = service.generate_capsule(
        CapsuleWardrobeRequest(
            season="Лето",
            max_outfits=4,
            target_item_limit=6,
            catalog=[
                WardrobeCatalogItemInput(
                    id=1,
                    sku="TOP-001",
                    name="Fine Knit Tee",
                    display_category="База",
                    season_tags=["Лето"],
                    color="white",
                    is_available=True,
                    is_active=True,
                ),
                WardrobeCatalogItemInput(
                    id=2,
                    sku="TOP-002",
                    name="Soft Cardigan",
                    display_category="Кардиганы и кофты",
                    season_tags=["Лето", "Весна"],
                    color="gray",
                    is_available=True,
                    is_active=True,
                ),
                WardrobeCatalogItemInput(
                    id=3,
                    sku="BOT-001",
                    name="Relaxed Trousers",
                    display_category="Брюки",
                    season_tags=["Лето"],
                    color="beige",
                    is_available=True,
                    is_active=True,
                ),
                WardrobeCatalogItemInput(
                    id=4,
                    sku="BOT-002",
                    name="Straight Skirt",
                    display_category="Юбки",
                    season_tags=["Лето"],
                    color="black",
                    is_available=True,
                    is_active=True,
                ),
                WardrobeCatalogItemInput(
                    id=5,
                    sku="OUT-001",
                    name="Minimal Coat",
                    display_category="Верхняя одежда",
                    season_tags=["Лето", "Весна"],
                    color="gray",
                    is_available=True,
                    is_active=True,
                ),
                WardrobeCatalogItemInput(
                    id=6,
                    sku="TOP-003",
                    name="Accent Blouse",
                    display_category="Блузы",
                    season_tags=["Лето"],
                    color="red",
                    is_available=True,
                    is_active=True,
                ),
            ],
        )
    )

    assert 1 <= len(result.outfits) <= 4
    assert len(result.capsule_items) <= 6
    assert any(item.normalized_category == "outerwear" for item in result.capsule_items)
    for outfit in result.outfits:
        assert len(set(outfit.colors)) <= 3
        assert len(outfit.explanation) > 0
        assert {item.normalized_category for item in outfit.items}.issuperset({"top", "bottom"})
