from sqlalchemy import inspect, text


def test_initialize_database_adds_body_profile_columns_to_legacy_users_table() -> None:
    from app.core.database import engine, initialize_database

    initialize_database(reset=True)

    with engine.begin() as connection:
        connection.execute(text("DROP TABLE IF EXISTS users"))
        connection.execute(
            text(
                """
                CREATE TABLE users (
                    id INTEGER PRIMARY KEY,
                    email VARCHAR(255) NOT NULL UNIQUE,
                    full_name VARCHAR(255) NOT NULL,
                    hashed_password VARCHAR(255) NOT NULL,
                    role VARCHAR(32) NOT NULL,
                    is_active BOOLEAN NOT NULL DEFAULT 1
                )
                """
            )
        )

    initialize_database()

    user_columns = {column["name"] for column in inspect(engine).get_columns("users")}

    assert {
        "preferred_language",
        "height_cm",
        "weight_kg",
        "chest_cm",
        "waist_cm",
        "hips_cm",
        "preferred_fit",
        "alpha_size",
        "top_size",
        "bottom_size",
        "dress_size",
    }.issubset(user_columns)


def test_initialize_database_adds_timestamp_columns_to_legacy_users_table() -> None:
    from app.core.database import engine, initialize_database

    initialize_database(reset=True)

    with engine.begin() as connection:
        connection.execute(text("DROP TABLE IF EXISTS users"))
        connection.execute(
            text(
                """
                CREATE TABLE users (
                    id INTEGER PRIMARY KEY,
                    email VARCHAR(255) NOT NULL UNIQUE,
                    full_name VARCHAR(255) NOT NULL,
                    hashed_password VARCHAR(255) NOT NULL,
                    role VARCHAR(32) NOT NULL,
                    is_active BOOLEAN NOT NULL DEFAULT 1
                )
                """
            )
        )

    initialize_database()

    user_columns = {column["name"] for column in inspect(engine).get_columns("users")}

    assert {"created_at", "updated_at"}.issubset(user_columns)
