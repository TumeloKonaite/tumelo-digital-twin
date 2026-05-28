from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.app.core.config import Settings
from src.app.main import create_app


@pytest.fixture
def content_data_dir(tmp_path: Path) -> Path:
    data_dir = tmp_path / "data"
    conversations_dir = data_dir / "conversations"
    conversations_dir.mkdir(parents=True)

    (data_dir / "twin_profile.json").write_text(
        json.dumps(
            {
                "name": "Tumelo",
                "full_name": "Tumelo Tshana Konaite",
                "email": "tumelo@example.com",
                "linkedin": "linkedin.com/in/tumelo",
                "github": "github.com/tumelo",
            }
        ),
        encoding="utf-8",
    )
    (data_dir / "summary.txt").write_text("Builds backend systems.", encoding="utf-8")
    (data_dir / "style.txt").write_text("Warm, concise, and direct.", encoding="utf-8")
    (data_dir / "fallback_personality.txt").write_text(
        "Fallback personality",
        encoding="utf-8",
    )
    return data_dir


@pytest.fixture
def settings(content_data_dir: Path) -> Settings:
    return Settings(
        openai_api_key="test-key",
        content_data_dir=content_data_dir,
        conversation_storage_dir=content_data_dir / "conversations",
    )


@pytest.fixture
def app(settings: Settings):
    return create_app(settings=settings)


@pytest.fixture
def client(app):
    with TestClient(app) as test_client:
        yield test_client
