from pathlib import Path


def test_settings_resolve_relative_database_and_media_paths_to_project_root(monkeypatch) -> None:
    from app.core.config import PROJECT_ROOT, Settings

    monkeypatch.setenv("DATABASE_URL", "sqlite:///./fashion.db")
    monkeypatch.setenv("MEDIA_ROOT", "media")

    settings = Settings(_env_file=None)

    assert settings.database_url == f"sqlite:///{(PROJECT_ROOT / 'fashion.db').resolve().as_posix()}"
    assert settings.media_root == str((PROJECT_ROOT / "media").resolve())


def test_settings_keep_absolute_database_url_unchanged(monkeypatch, tmp_path: Path) -> None:
    from app.core.config import Settings

    absolute_database_url = f"sqlite:///{(tmp_path / 'custom.db').as_posix()}"
    monkeypatch.setenv("DATABASE_URL", absolute_database_url)

    settings = Settings(_env_file=None)

    assert settings.database_url == absolute_database_url
