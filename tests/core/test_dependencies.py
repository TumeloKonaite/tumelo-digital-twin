from __future__ import annotations

import logging
from pathlib import Path

from fastapi import FastAPI, Request
from sqlalchemy.orm import Session

from src.app.core.config import Settings
from src.app.core.dependencies import (
    AppDependencies,
    build_dependencies,
    build_session_factory,
    get_contact_service,
    initialize_dependencies,
)
from src.app.domain.contact import ContactService
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
        dependencies = build_dependencies(settings)

    assert isinstance(dependencies.contact_repository, NullContactRepository)
    assert dependencies.database_engine is None
    assert dependencies.session_factory is None
    assert "DATABASE_URL is not configured" in caplog.text


def test_dependency_container_builds_postgres_repository_with_database_url(
    tmp_path: Path,
) -> None:
    settings = _settings(tmp_path, database_url="sqlite+pysqlite:///:memory:")

    dependencies = build_dependencies(settings)

    assert isinstance(dependencies, AppDependencies)
    assert dependencies.database_engine is not None
    assert dependencies.session_factory is not None
    assert not isinstance(dependencies.session_factory, Session)
    assert isinstance(dependencies.contact_repository, PostgresContactRepository)
    assert isinstance(dependencies.contact_service, ContactService)
    assert dependencies.contact_service._repository is dependencies.contact_repository


def test_build_session_factory_returns_none_without_engine() -> None:
    assert build_session_factory(None) is None


def test_initialize_dependencies_stores_container_on_app_state(
    tmp_path: Path,
) -> None:
    app = FastAPI()
    settings = _settings(tmp_path, database_url="sqlite+pysqlite:///:memory:")

    dependencies = initialize_dependencies(app, settings=settings)

    assert app.state.dependencies is dependencies
    assert (
        app.state.dependencies.contact_service._repository
        is app.state.dependencies.contact_repository
    )


def test_get_contact_service_resolves_from_container(tmp_path: Path) -> None:
    app = FastAPI()
    settings = _settings(tmp_path, database_url="sqlite+pysqlite:///:memory:")
    initialize_dependencies(app, settings=settings)
    request = Request({"type": "http", "app": app})

    service = get_contact_service(request)

    assert service is app.state.dependencies.contact_service
