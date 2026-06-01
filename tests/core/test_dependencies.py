from __future__ import annotations

import logging
from pathlib import Path

from src.app.core.config import Settings
from src.app.core.dependencies import build_contact_repository
from src.app.infrastructure.contact import (
    NullContactRepository,
    PostgresContactRepository,
)


def _settings(
    tmp_path: Path,
    *,
    database_url: str | None,
) -> Settings:
    data_dir = tmp_path / "data"
    conversations_dir = data_dir / "conversations"
    conversations_dir.mkdir(parents=True)
    return Settings(
        openai_api_key="test-key",
        database_url=database_url,
        content_data_dir=data_dir,
        conversation_storage_dir=conversations_dir,
    )


def test_build_contact_repository_returns_null_repository_without_database_url(
    tmp_path: Path,
    caplog,
) -> None:
    settings = _settings(tmp_path, database_url=None)

    with caplog.at_level(logging.WARNING):
        repository = build_contact_repository(settings)

    assert isinstance(repository, NullContactRepository)
    assert "DATABASE_URL is not configured" in caplog.text


def test_build_contact_repository_returns_postgres_repository_with_database_url(
    tmp_path: Path,
) -> None:
    settings = _settings(tmp_path, database_url="sqlite+pysqlite:///:memory:")

    repository = build_contact_repository(settings)

    assert isinstance(repository, PostgresContactRepository)
