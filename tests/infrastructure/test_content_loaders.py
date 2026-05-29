from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from src.app.core.content_paths import (
    LINKEDIN_FILENAME,
    STYLE_FILENAME,
    SUMMARY_FILENAME,
    TWIN_PROFILE_FILENAME,
)
from src.app.infrastructure.content import (
    FactsLoader,
    InvalidContentError,
    ResourceLoader,
)
from src.app.infrastructure.content.resource_loader import LINKEDIN_NOT_AVAILABLE


def test_facts_loader_reads_profile_from_configured_data_dir(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / TWIN_PROFILE_FILENAME).write_text(
        json.dumps(
            {
                "name": "Tumelo",
                "full_name": "Tumelo Tshana Konaite",
                "email": "tumelo@example.com",
            }
        ),
        encoding="utf-8",
    )

    loader = FactsLoader(data_dir)

    facts = loader.load()

    assert facts["name"] == "Tumelo"
    assert facts["full_name"] == "Tumelo Tshana Konaite"
    assert loader.path == data_dir / TWIN_PROFILE_FILENAME


def test_facts_loader_raises_clear_error_when_required_fields_are_missing(
    tmp_path: Path,
) -> None:
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / TWIN_PROFILE_FILENAME).write_text(
        json.dumps({"name": "Tumelo"}),
        encoding="utf-8",
    )

    with pytest.raises(InvalidContentError, match="Missing required profile fields"):
        FactsLoader(data_dir).load()


def test_resource_loader_reads_summary_style_and_fallback(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / SUMMARY_FILENAME).write_text("Summary text", encoding="utf-8")
    (data_dir / STYLE_FILENAME).write_text("Style text", encoding="utf-8")
    (data_dir / "fallback_personality.txt").write_text(
        "Fallback text", encoding="utf-8"
    )

    loader = ResourceLoader(data_dir)

    assert loader.load_summary() == "Summary text"
    assert loader.load_style() == "Style text"
    assert loader.load_fallback_personality() == "Fallback text"


def test_resource_loader_returns_placeholder_when_linkedin_pdf_is_missing(
    tmp_path: Path,
) -> None:
    data_dir = tmp_path / "data"
    data_dir.mkdir()

    assert ResourceLoader(data_dir).load_linkedin() == LINKEDIN_NOT_AVAILABLE


def test_resource_loader_extracts_text_from_linkedin_pdf(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / LINKEDIN_FILENAME).write_bytes(b"%PDF-1.4")
    reader = Mock()
    reader.pages = [
        Mock(extract_text=Mock(return_value="Page one ")),
        Mock(extract_text=Mock(return_value="Page two")),
    ]

    with patch(
        "src.app.infrastructure.content.resource_loader.PdfReader", return_value=reader
    ) as pdf_reader:
        linkedin = ResourceLoader(data_dir).load_linkedin()

    assert linkedin == "Page one Page two"
    pdf_reader.assert_called_once_with(str(data_dir / LINKEDIN_FILENAME))


def test_resource_loader_builds_prompt_context_from_loaded_resources(
    tmp_path: Path,
) -> None:
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / SUMMARY_FILENAME).write_text("Summary", encoding="utf-8")
    (data_dir / STYLE_FILENAME).write_text("Style", encoding="utf-8")
    (data_dir / TWIN_PROFILE_FILENAME).write_text(
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

    context = ResourceLoader(data_dir).build_prompt_context(
        now=datetime(2026, 5, 28, 9, 30, 0)
    )

    assert context["name"] == "Tumelo"
    assert context["full_name"] == "Tumelo Tshana Konaite"
    assert context["summary"] == "Summary"
    assert context["style"] == "Style"
    assert context["linkedin"] == LINKEDIN_NOT_AVAILABLE
    assert "tumelo@example.com" in context["contact_links"]
    assert "https://linkedin.com/in/tumelo" in context["contact_links"]
    assert "https://github.com/tumelo" in context["contact_links"]
    assert context["current_datetime"] == "2026-05-28 09:30:00"
