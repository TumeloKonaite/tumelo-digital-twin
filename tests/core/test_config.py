from __future__ import annotations

import importlib
from pathlib import Path

from src.app.core.config import Settings


def test_settings_load_database_url_from_environment(
    monkeypatch,
    tmp_path: Path,
) -> None:
    data_dir = tmp_path / "data"
    conversations_dir = data_dir / "conversations"
    conversations_dir.mkdir(parents=True)

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://user:pass@localhost/db")
    monkeypatch.setenv("CONTENT_DATA_DIR", str(data_dir))
    monkeypatch.setenv("CONVERSATION_STORAGE_DIR", str(conversations_dir))

    settings = Settings()

    assert settings.database_url == "postgresql+psycopg://user:pass@localhost/db"


def test_app_import_does_not_require_database_connection(
    monkeypatch,
    tmp_path: Path,
) -> None:
    data_dir = tmp_path / "data"
    conversations_dir = data_dir / "conversations"
    conversations_dir.mkdir(parents=True)

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+psycopg://user:pass@invalid-host-for-import-test/neondb",
    )
    monkeypatch.setenv("CONTENT_DATA_DIR", str(data_dir))
    monkeypatch.setenv("CONVERSATION_STORAGE_DIR", str(conversations_dir))

    import src.app.main as main_module

    reloaded = importlib.reload(main_module)

    assert reloaded.app is not None


def test_settings_allow_missing_openai_api_key(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    conversations_dir = data_dir / "conversations"
    conversations_dir.mkdir(parents=True)

    settings = Settings(
        openai_api_key=None,
        content_data_dir=data_dir,
        conversation_storage_dir=conversations_dir,
    )

    assert settings.openai_api_key is None
