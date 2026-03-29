from pathlib import Path
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator

from app.domain.language import DEFAULT_LANGUAGE

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    app_name: str = "Fashion Pre-Order MVP API"
    api_v1_prefix: str = "/api/v1"
    websocket_prefix: str = "/ws"
    cors_origins: list[str] = [
        "http://localhost:8081",
        "http://127.0.0.1:8081",
        "http://localhost:19006",
        "http://127.0.0.1:19006",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]
    catalog_seed_mode: str = "demo"
    default_language: str = DEFAULT_LANGUAGE.value
    database_url: str = f"sqlite:///{(PROJECT_ROOT / 'fashion.db').as_posix()}"
    secret_key: str = "change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    branch_review_sla_minutes: int = 120
    production_start_sla_minutes: int = 480
    production_completion_sla_minutes: int = 2880
    max_branch_assignment_attempts: int = 3
    media_root: str = "media"
    media_url_prefix: str = "/media"
    try_on_max_upload_bytes: int = 10 * 1024 * 1024
    try_on_provider_timeout_seconds: int = 120
    try_on_max_attempts: int = 3
    flux_api_url: str | None = None
    ai_enabled: bool = True
    ai_try_on_enabled: bool = True
    ai_stylist_enabled: bool = True
    ai_size_explanations_enabled: bool = True
    ai_capsule_explanations_enabled: bool = True
    ai_outfit_rerank_enabled: bool = True
    openrouter_api_key: str | None = None
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    ai_text_model: str = "arcee-ai/trinity-large-preview:free"
    ai_text_temperature: float = 0.0
    ai_text_top_p: float = 1.0
    ai_text_timeout_seconds: int = 45
    ai_try_on_primary_model: str = "google/gemini-2.5-flash-image"
    ai_try_on_fallback_model: str = "black-forest-labs/flux.2-flex"
    ai_try_on_timeout_seconds: int = 120
    ai_try_on_max_attempts: int = 2

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @field_validator("catalog_seed_mode")
    @classmethod
    def validate_catalog_seed_mode(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in {"demo", "prod"}:
            raise ValueError("catalog_seed_mode must be 'demo' or 'prod'")
        return normalized

    @field_validator("database_url")
    @classmethod
    def normalize_database_url(cls, value: str) -> str:
        prefix = "sqlite:///"
        if not value.startswith(prefix):
            return value
        database_name = value.removeprefix(prefix)
        if database_name == ":memory:":
            return value
        database_path = Path(database_name)
        if database_path.is_absolute():
            return value
        return f"{prefix}{(PROJECT_ROOT / database_path).resolve().as_posix()}"

    @field_validator("media_root")
    @classmethod
    def normalize_media_root(cls, value: str) -> str:
        media_path = Path(value)
        if media_path.is_absolute():
            return value
        return str((PROJECT_ROOT / media_path).resolve())


@lru_cache
def get_settings() -> Settings:
    return Settings()
