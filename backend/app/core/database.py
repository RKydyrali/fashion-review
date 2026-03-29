import sqlite3
from collections.abc import Generator
from pathlib import Path

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import NullPool
from sqlalchemy import select

from app.core.config import get_settings
from app.domain.language import LanguageCode
from app.seed.demo_data import DEMO_COLLECTIONS, DEMO_PRODUCTS, DEMO_SIZE_CHARTS
from app.seed.prod_data import PROD_COLLECTIONS, PROD_PRODUCTS

settings = get_settings()

connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine_kwargs = {"future": True, "connect_args": connect_args}
if settings.database_url.startswith("sqlite"):
    engine_kwargs["poolclass"] = NullPool
engine = create_engine(settings.database_url, **engine_kwargs)
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    future=True,
    class_=Session,
)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _apply_lightweight_migrations() -> None:
    inspector = inspect(engine)
    table_names = inspector.get_table_names()

    def ensure_timestamp_columns(table_name: str) -> None:
        if table_name not in table_names:
            return
        existing_columns = {column["name"] for column in inspector.get_columns(table_name)}
        for column_name in ("created_at", "updated_at"):
            if column_name in existing_columns:
                continue
            with engine.begin() as connection:
                connection.execute(
                    text(
                        f"ALTER TABLE {table_name} ADD COLUMN {column_name} DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP"
                    )
                )

    for timestamped_table in ("users", "products", "collections", "branches", "orders", "preorder_batches"):
        ensure_timestamp_columns(timestamped_table)

    if "users" in table_names:
        user_columns = {column["name"] for column in inspector.get_columns("users")}
        for column_name, ddl in (
            ("preferred_language", "ALTER TABLE users ADD COLUMN preferred_language VARCHAR(2) NOT NULL DEFAULT 'ru'"),
            ("height_cm", "ALTER TABLE users ADD COLUMN height_cm FLOAT"),
            ("weight_kg", "ALTER TABLE users ADD COLUMN weight_kg FLOAT"),
            ("chest_cm", "ALTER TABLE users ADD COLUMN chest_cm FLOAT"),
            ("waist_cm", "ALTER TABLE users ADD COLUMN waist_cm FLOAT"),
            ("hips_cm", "ALTER TABLE users ADD COLUMN hips_cm FLOAT"),
            ("preferred_fit", "ALTER TABLE users ADD COLUMN preferred_fit VARCHAR(16)"),
            ("alpha_size", "ALTER TABLE users ADD COLUMN alpha_size VARCHAR(32)"),
            ("top_size", "ALTER TABLE users ADD COLUMN top_size VARCHAR(32)"),
            ("bottom_size", "ALTER TABLE users ADD COLUMN bottom_size VARCHAR(32)"),
            ("dress_size", "ALTER TABLE users ADD COLUMN dress_size VARCHAR(32)"),
        ):
            if column_name in user_columns:
                continue
            with engine.begin() as connection:
                connection.execute(text(ddl))

    if "products" in table_names:
        product_columns = {column["name"] for column in inspector.get_columns("products")}
        for column_name, ddl in (
            ("slug", "ALTER TABLE products ADD COLUMN slug VARCHAR(160) NOT NULL DEFAULT ''"),
            ("subtitle", "ALTER TABLE products ADD COLUMN subtitle VARCHAR(255)"),
            ("long_description", "ALTER TABLE products ADD COLUMN long_description TEXT"),
            ("base_price_minor", "ALTER TABLE products ADD COLUMN base_price_minor INTEGER NOT NULL DEFAULT 0"),
            ("currency", "ALTER TABLE products ADD COLUMN currency VARCHAR(3) NOT NULL DEFAULT 'USD'"),
            ("collection_slug", "ALTER TABLE products ADD COLUMN collection_slug VARCHAR(120)"),
            ("hero_image_url", "ALTER TABLE products ADD COLUMN hero_image_url VARCHAR(500)"),
            ("gallery_image_urls", "ALTER TABLE products ADD COLUMN gallery_image_urls JSON NOT NULL DEFAULT '[]'"),
            ("fabric_notes", "ALTER TABLE products ADD COLUMN fabric_notes TEXT"),
            ("care_notes", "ALTER TABLE products ADD COLUMN care_notes TEXT"),
            ("preorder_note", "ALTER TABLE products ADD COLUMN preorder_note TEXT"),
            ("available_sizes", "ALTER TABLE products ADD COLUMN available_sizes JSON NOT NULL DEFAULT '[]'"),
            ("size_chart_id", "ALTER TABLE products ADD COLUMN size_chart_id INTEGER"),
            ("editorial_rank", "ALTER TABLE products ADD COLUMN editorial_rank INTEGER NOT NULL DEFAULT 1"),
            ("is_featured", "ALTER TABLE products ADD COLUMN is_featured BOOLEAN NOT NULL DEFAULT 0"),
        ):
            if column_name in product_columns:
                continue
            with engine.begin() as connection:
                connection.execute(text(ddl))

    if "collections" in table_names:
        collection_columns = {column["name"] for column in inspector.get_columns("collections")}
        if "is_active" not in collection_columns:
            with engine.begin() as connection:
                connection.execute(text("ALTER TABLE collections ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT 1"))

    if "branches" in table_names:
        branch_columns = inspector.get_columns("branches")
        manager_column = next((column for column in branch_columns if column["name"] == "manager_user_id"), None)
        if manager_column is not None and manager_column.get("nullable") is False and settings.database_url.startswith("sqlite"):
            with engine.begin() as connection:
                connection.execute(text("PRAGMA foreign_keys=OFF"))
                connection.execute(
                    text(
                        """
                        CREATE TABLE branches__new (
                            id INTEGER PRIMARY KEY,
                            name VARCHAR(255) NOT NULL,
                            code VARCHAR(50) NOT NULL UNIQUE,
                            city VARCHAR(120) NOT NULL,
                            manager_user_id INTEGER NULL,
                            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY(manager_user_id) REFERENCES users (id)
                        )
                        """
                    )
                )
                connection.execute(
                    text(
                        """
                        INSERT INTO branches__new (id, name, code, city, manager_user_id, created_at, updated_at)
                        SELECT id, name, code, city, manager_user_id, created_at, updated_at
                        FROM branches
                        """
                    )
                )
                connection.execute(text("DROP TABLE branches"))
                connection.execute(text("ALTER TABLE branches__new RENAME TO branches"))
                connection.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_branches_code ON branches (code)"))
                connection.execute(text("PRAGMA foreign_keys=ON"))

    if "product_translations" in table_names:
        translation_columns = {column["name"] for column in inspector.get_columns("product_translations")}
        for column_name, ddl in (
            ("subtitle", "ALTER TABLE product_translations ADD COLUMN subtitle VARCHAR(255)"),
            ("long_description", "ALTER TABLE product_translations ADD COLUMN long_description TEXT"),
            ("fabric_notes", "ALTER TABLE product_translations ADD COLUMN fabric_notes TEXT"),
            ("care_notes", "ALTER TABLE product_translations ADD COLUMN care_notes TEXT"),
            ("preorder_note", "ALTER TABLE product_translations ADD COLUMN preorder_note TEXT"),
        ):
            if column_name in translation_columns:
                continue
            with engine.begin() as connection:
                connection.execute(text(ddl))

    if "orders" in table_names:
        order_columns = {column["name"] for column in inspector.get_columns("orders")}
        for column_name, ddl in (
            ("preorder_batch_id", "ALTER TABLE orders ADD COLUMN preorder_batch_id INTEGER"),
            ("size_label", "ALTER TABLE orders ADD COLUMN size_label VARCHAR(16)"),
            ("unit_price_minor", "ALTER TABLE orders ADD COLUMN unit_price_minor INTEGER NOT NULL DEFAULT 0"),
            ("tailoring_adjustment_minor", "ALTER TABLE orders ADD COLUMN tailoring_adjustment_minor INTEGER NOT NULL DEFAULT 0"),
            ("total_price_minor", "ALTER TABLE orders ADD COLUMN total_price_minor INTEGER NOT NULL DEFAULT 0"),
            ("currency", "ALTER TABLE orders ADD COLUMN currency VARCHAR(3) NOT NULL DEFAULT 'USD'"),
        ):
            if column_name in order_columns:
                continue
            with engine.begin() as connection:
                connection.execute(text(ddl))


def initialize_database(*, reset: bool = False) -> None:
    import app.models  # noqa: F401
    from app.models.base import Base

    if reset:
        _reset_database_file()
        remaining_tables = inspect(engine).get_table_names()
        if remaining_tables:
            with engine.begin() as connection:
                if settings.database_url.startswith("sqlite"):
                    connection.execute(text("PRAGMA foreign_keys=OFF"))
                for table_name in remaining_tables:
                    connection.execute(text(f'DROP TABLE IF EXISTS "{table_name}"'))
                if settings.database_url.startswith("sqlite"):
                    connection.execute(text("PRAGMA foreign_keys=ON"))
    Base.metadata.create_all(bind=engine)
    _apply_lightweight_migrations()


def _reset_database_file() -> None:
    engine.dispose()
    if not settings.database_url.startswith("sqlite:///"):
        inspector = inspect(engine)
        table_names = inspector.get_table_names()
        if not table_names:
            return
        with engine.begin() as connection:
            for table_name in table_names:
                connection.execute(text(f'DROP TABLE IF EXISTS "{table_name}"'))
        return

    database_name = settings.database_url.removeprefix("sqlite:///")
    if database_name == ":memory:":
        return
    database_path = Path(database_name)
    if not database_path.is_absolute():
        database_path = Path.cwd() / database_path
    if not database_path.exists():
        return

    with sqlite3.connect(database_path) as connection:
        cursor = connection.cursor()
        cursor.execute("PRAGMA foreign_keys=OFF")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        table_names = [row[0] for row in cursor.fetchall() if row[0] != "sqlite_sequence"]
        for table_name in table_names:
            cursor.execute(f'DROP TABLE IF EXISTS "{table_name}"')
        connection.commit()


def seed_demo_users() -> None:
    from app.core.security import get_password_hash, verify_password
    from app.domain.roles import UserRole
    from app.models.user import User

    demo_users = [
        {
            "id": 10,
            "email": "admin@gmail.com",
            "full_name": "Admin",
            "password": "admin",
            "role": UserRole.ADMIN,
            "preferred_language": LanguageCode.EN.value,
            "is_active": True,
        },
        {
            "id": 1,
            "email": "client@example.com",
            "full_name": "Client Demo",
            "password": "clientpass123",
            "role": UserRole.CLIENT,
            "preferred_language": LanguageCode.RU.value,
            "is_active": True,
        },
        {
            "id": 2,
            "email": "franchise@example.com",
            "full_name": "Franchise Demo",
            "password": "franchisepass123",
            "role": UserRole.FRANCHISEE,
            "preferred_language": LanguageCode.KK.value,
            "is_active": True,
        },
        {
            "id": 3,
            "email": "production@example.com",
            "full_name": "Production Demo",
            "password": "productionpass123",
            "role": UserRole.PRODUCTION,
            "preferred_language": LanguageCode.EN.value,
            "is_active": True,
        },
        {
            "id": 4,
            "email": "inactive@example.com",
            "full_name": "Inactive Demo",
            "password": "inactivepass123",
            "role": UserRole.CLIENT,
            "preferred_language": LanguageCode.RU.value,
            "is_active": False,
        },
    ]

    with SessionLocal() as session:
        for demo_user in demo_users:
            existing_user = session.execute(
                select(User).where(User.email == demo_user["email"])
            ).scalar_one_or_none()

            if existing_user is None:
                session.add(
                    User(
                        id=demo_user["id"],
                        email=demo_user["email"],
                        full_name=demo_user["full_name"],
                        hashed_password=get_password_hash(demo_user["password"]),
                        role=demo_user["role"],
                        preferred_language=demo_user["preferred_language"],
                        is_active=demo_user["is_active"],
                    )
                )
                continue

            if existing_user.full_name != demo_user["full_name"]:
                existing_user.full_name = demo_user["full_name"]
            if not verify_password(demo_user["password"], existing_user.hashed_password):
                existing_user.hashed_password = get_password_hash(demo_user["password"])
            if existing_user.role != demo_user["role"]:
                existing_user.role = demo_user["role"]
            if existing_user.preferred_language != demo_user["preferred_language"]:
                existing_user.preferred_language = demo_user["preferred_language"]
            if existing_user.is_active != demo_user["is_active"]:
                existing_user.is_active = demo_user["is_active"]
        session.commit()


def _get_catalog_seed_payload(mode: str | None = None) -> tuple[list[dict], list[dict]]:
    selected_mode = mode or settings.catalog_seed_mode
    if selected_mode == "prod":
        return PROD_COLLECTIONS, PROD_PRODUCTS
    return DEMO_COLLECTIONS, DEMO_PRODUCTS


def clear_seed_catalog() -> None:
    from app.models.collection import Collection
    from app.models.product import Product

    seeded_collection_ids = {item["id"] for item in DEMO_COLLECTIONS} | {item["id"] for item in PROD_COLLECTIONS}
    seeded_product_ids = {item["id"] for item in DEMO_PRODUCTS} | {item["id"] for item in PROD_PRODUCTS}
    seeded_collection_slugs = {item["slug"] for item in DEMO_COLLECTIONS} | {item["slug"] for item in PROD_COLLECTIONS}
    seeded_product_slugs = {item["slug"] for item in DEMO_PRODUCTS} | {item["slug"] for item in PROD_PRODUCTS}

    with SessionLocal() as session:
        seeded_products = list(
            session.scalars(
                select(Product).where(
                    Product.id.in_(seeded_product_ids) | Product.slug.in_(seeded_product_slugs)
                )
            )
        )
        for product in seeded_products:
            session.delete(product)

        seeded_collections = list(
            session.scalars(
                select(Collection).where(
                    Collection.id.in_(seeded_collection_ids) | Collection.slug.in_(seeded_collection_slugs)
                )
            )
        )
        for collection in seeded_collections:
            session.delete(collection)
        session.commit()


def seed_default_branch() -> None:
    from app.models.branch import Branch

    with SessionLocal() as session:
        session.merge(Branch(id=1, name="Central Branch", code="CTR", city="Almaty", manager_user_id=2))
        session.commit()


def seed_catalog() -> None:
    from app.models.branch import Branch
    from app.models.collection import Collection
    from app.models.product import Product
    from app.models.product_translation import ProductTranslation

    collections, products = _get_catalog_seed_payload()

    with SessionLocal() as session:
        for collection_data in collections:
            session.merge(Collection(**collection_data))

        for product_data in products:
            translation_rows = product_data["translations"]
            product_payload = {key: value for key, value in product_data.items() if key != "translations"}
            session.merge(Product(**product_payload))
            for translation_data in translation_rows:
                session.merge(ProductTranslation(product_id=product_payload["id"], **translation_data))

        session.merge(Branch(id=1, name="Central Branch", code="CTR", city="Almaty", manager_user_id=2))
        session.commit()


def seed_demo_catalog() -> None:
    seed_catalog()


def seed_demo_size_charts() -> None:
    from app.models.size_chart import SizeChartRecord

    with SessionLocal() as session:
        for chart_data in DEMO_SIZE_CHARTS:
            session.merge(SizeChartRecord(**chart_data))
        session.commit()
