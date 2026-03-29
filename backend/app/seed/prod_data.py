"""Production catalog seed data.

Replace these lists with your real collections and products, then set
CATALOG_SEED_MODE=prod in the backend environment.
"""

PROD_COLLECTIONS: list[dict] = [
    {
        "id": 101,
        "slug": "prod-signature-collection",
        "hero_image_url": "https://your-cdn.example.com/collections/signature-hero.jpg",
        "cover_image_url": "https://your-cdn.example.com/collections/signature-cover.jpg",
        "sort_order": 1,
        "is_featured": True,
        "name_translations": {
            "en": "SIGNATURE COLLECTION",
            "ru": "ФИРМЕННАЯ КОЛЛЕКЦИЯ",
            "kk": "ҚОЛТАҢБА ЖИНАҒЫ",
        },
        "summary_translations": {
            "en": "REPLACE THIS WITH YOUR REAL COLLECTION SUMMARY.",
            "ru": "ЗАМЕНИТЕ ЭТО РЕАЛЬНЫМ ОПИСАНИЕМ КОЛЛЕКЦИИ.",
            "kk": "МҰНЫ НАҚТЫ ЖИНАҚ СИПАТТАМАСЫМЕН АУЫСТЫРЫҢЫЗ.",
        },
        "eyebrow_translations": {
            "en": "COLLECTION 01",
            "ru": "КОЛЛЕКЦИЯ 01",
            "kk": "ЖИНАҚ 01",
        },
    }
]

PROD_PRODUCTS: list[dict] = [
    {
        "id": 1001,
        "sku": "PROD-001",
        "slug": "prod-signature-item",
        "name": "SIGNATURE ITEM",
        "display_category": "TOPS",
        "normalized_category": "top",
        "season_tags": ["seasonless"],
        "color": "black",
        "subtitle": "REPLACE WITH YOUR PRODUCT SUBTITLE.",
        "long_description": "REPLACE WITH YOUR PRODUCT DESCRIPTION.",
        "base_price_minor": 100000,
        "currency": "USD",
        "collection_slug": "prod-signature-collection",
        "hero_image_url": "https://your-cdn.example.com/products/prod-001-hero.jpg",
        "gallery_image_urls": [
            "https://your-cdn.example.com/products/prod-001-1.jpg",
            "https://your-cdn.example.com/products/prod-001-2.jpg",
        ],
        "fabric_notes": "REPLACE WITH FABRIC NOTES.",
        "care_notes": "REPLACE WITH CARE NOTES.",
        "preorder_note": "REPLACE WITH PREORDER NOTE.",
        "available_sizes": ["XS", "S", "M", "L", "XL"],
        "size_chart_id": 1,
        "editorial_rank": 1,
        "is_featured": True,
        "reference_image_url": "https://your-cdn.example.com/products/prod-001-ref.jpg",
        "is_available": True,
        "is_active": True,
        "translations": [
            {
                "language_code": "en",
                "name": "SIGNATURE ITEM",
                "description": "REPLACE WITH ENGLISH DESCRIPTION.",
                "subtitle": "REPLACE WITH ENGLISH SUBTITLE.",
                "long_description": "REPLACE WITH ENGLISH LONG DESCRIPTION.",
                "fabric_notes": "REPLACE WITH ENGLISH FABRIC NOTES.",
                "care_notes": "REPLACE WITH ENGLISH CARE NOTES.",
                "preorder_note": "REPLACE WITH ENGLISH PREORDER NOTE.",
                "display_category": "TOPS",
            },
            {
                "language_code": "ru",
                "name": "ФИРМЕННОЕ ИЗДЕЛИЕ",
                "description": "ЗАМЕНИТЕ НА РУССКОЕ ОПИСАНИЕ.",
                "subtitle": "ЗАМЕНИТЕ НА РУССКИЙ ПОДЗАГОЛОВОК.",
                "long_description": "ЗАМЕНИТЕ НА РУССКОЕ ПОДРОБНОЕ ОПИСАНИЕ.",
                "fabric_notes": "ЗАМЕНИТЕ НА ОПИСАНИЕ ТКАНИ.",
                "care_notes": "ЗАМЕНИТЕ НА УХОД.",
                "preorder_note": "ЗАМЕНИТЕ НА ПРИМЕЧАНИЕ ПРЕДЗАКАЗА.",
                "display_category": "ТОПЫ",
            },
            {
                "language_code": "kk",
                "name": "ҚОЛТАҢБА БҰЙЫМЫ",
                "description": "МҰНЫ ҚАЗАҚША СИПАТТАМАМЕН АУЫСТЫРЫҢЫЗ.",
                "subtitle": "МҰНЫ ҚАЗАҚША ҚЫСҚА МӘТІНМЕН АУЫСТЫРЫҢЫЗ.",
                "long_description": "МҰНЫ ҚАЗАҚША ТОЛЫҚ СИПАТТАМАМЕН АУЫСТЫРЫҢЫЗ.",
                "fabric_notes": "МАТА ТУРАЛЫ АҚПАРАТТЫ АУЫСТЫРЫҢЫЗ.",
                "care_notes": "КҮТІМ АҚПАРАТЫН АУЫСТЫРЫҢЫЗ.",
                "preorder_note": "АЛДЫН АЛА ТАПСЫРЫС ЕСКЕРТПЕСІН АУЫСТЫРЫҢЫЗ.",
                "display_category": "ТОПТАР",
            },
        ],
    }
]
