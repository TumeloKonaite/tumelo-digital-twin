from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch

from src.app.core.config import PROJECT_ROOT
from src.app.core.content_paths import (
    FALLBACK_PERSONALITY_FILENAME,
    LINKEDIN_FILENAME,
    STYLE_FILENAME,
    SUMMARY_FILENAME,
    TWIN_PROFILE_FILENAME,
    resolve_data_dir,
    resolve_data_path,
)
from src.app.infrastructure.content import (
    FactsLoader,
    InvalidContentError,
    MissingContentError,
    ResourceLoader,
)
from src.app.infrastructure.content.resource_loader import LINKEDIN_NOT_AVAILABLE


class ContentPathResolutionTestCase(unittest.TestCase):
    def test_default_data_dir_resolves_to_repo_data_directory(self):
        self.assertEqual(resolve_data_dir(), PROJECT_ROOT / "data")

    def test_custom_data_path_resolves_under_provided_directory(self):
        custom_dir = Path(tempfile.gettempdir()) / "shadow-clone-test-data"

        self.assertEqual(
            resolve_data_path(SUMMARY_FILENAME, data_dir=custom_dir),
            custom_dir / SUMMARY_FILENAME,
        )


class FactsLoaderTestCase(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.data_dir = Path(self.temp_dir.name)
        self.loader = FactsLoader(self.data_dir)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_load_reads_profile_from_configured_data_dir(self):
        (self.data_dir / TWIN_PROFILE_FILENAME).write_text(
            json.dumps(
                {
                    "name": "Tumelo",
                    "full_name": "Tumelo Tshana Konaite",
                    "email": "tumelo@example.com",
                }
            ),
            encoding="utf-8",
        )

        facts = self.loader.load()

        self.assertEqual(facts["name"], "Tumelo")
        self.assertEqual(facts["full_name"], "Tumelo Tshana Konaite")
        self.assertEqual(self.loader.path, self.data_dir / TWIN_PROFILE_FILENAME)

    def test_load_raises_clear_error_when_profile_is_missing(self):
        with self.assertRaises(MissingContentError) as context:
            self.loader.load()

        self.assertIn("Required profile file not found", str(context.exception))
        self.assertIn(str(self.data_dir / TWIN_PROFILE_FILENAME), str(context.exception))

    def test_load_raises_clear_error_when_profile_json_is_invalid(self):
        (self.data_dir / TWIN_PROFILE_FILENAME).write_text("{invalid", encoding="utf-8")

        with self.assertRaises(InvalidContentError) as context:
            self.loader.load()

        self.assertIn("Invalid JSON in profile file", str(context.exception))

    def test_load_raises_clear_error_when_required_profile_fields_are_missing(self):
        (self.data_dir / TWIN_PROFILE_FILENAME).write_text(
            json.dumps({"name": "Tumelo"}),
            encoding="utf-8",
        )

        with self.assertRaises(InvalidContentError) as context:
            self.loader.load()

        self.assertIn("Missing required profile fields", str(context.exception))
        self.assertIn("full_name", str(context.exception))


class ResourceLoaderTextTestCase(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.data_dir = Path(self.temp_dir.name)
        self.loader = ResourceLoader(self.data_dir)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_load_summary_and_style_independently(self):
        (self.data_dir / SUMMARY_FILENAME).write_text("Summary text", encoding="utf-8")
        (self.data_dir / STYLE_FILENAME).write_text("Style text", encoding="utf-8")
        (self.data_dir / FALLBACK_PERSONALITY_FILENAME).write_text(
            "Fallback text",
            encoding="utf-8",
        )

        self.assertEqual(self.loader.load_summary(), "Summary text")
        self.assertEqual(self.loader.load_style(), "Style text")
        self.assertEqual(self.loader.load_fallback_personality(), "Fallback text")

    def test_load_summary_raises_clear_error_when_file_is_missing(self):
        with self.assertRaises(MissingContentError) as context:
            self.loader.load_summary()

        self.assertIn("Required summary file not found", str(context.exception))
        self.assertIn(str(self.data_dir / SUMMARY_FILENAME), str(context.exception))

    def test_load_style_raises_clear_error_when_file_is_unreadable(self):
        with patch.object(Path, "read_text", side_effect=OSError("permission denied")):
            with self.assertRaises(InvalidContentError) as context:
                self.loader.load_style()

        self.assertIn("Unable to read style file", str(context.exception))
        self.assertIn(str(self.data_dir / STYLE_FILENAME), str(context.exception))


class ResourceLoaderPdfTestCase(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.data_dir = Path(self.temp_dir.name)
        self._write_required_prompt_files()
        self.loader = ResourceLoader(self.data_dir)

    def tearDown(self):
        self.temp_dir.cleanup()

    def _write_required_prompt_files(self) -> None:
        (self.data_dir / SUMMARY_FILENAME).write_text("Summary", encoding="utf-8")
        (self.data_dir / STYLE_FILENAME).write_text("Style", encoding="utf-8")
        (self.data_dir / TWIN_PROFILE_FILENAME).write_text(
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

    def test_load_linkedin_returns_placeholder_when_pdf_is_missing(self):
        self.assertEqual(self.loader.load_linkedin(), LINKEDIN_NOT_AVAILABLE)

    def test_load_linkedin_extracts_text_from_pdf(self):
        (self.data_dir / LINKEDIN_FILENAME).write_bytes(b"%PDF-1.4")
        reader = Mock()
        reader.pages = [
            Mock(extract_text=Mock(return_value="Page one ")),
            Mock(extract_text=Mock(return_value="Page two")),
        ]

        with patch("src.app.infrastructure.content.resource_loader.PdfReader", return_value=reader) as pdf_reader:
            linkedin = self.loader.load_linkedin()

        self.assertEqual(linkedin, "Page one Page two")
        pdf_reader.assert_called_once_with(str(self.data_dir / LINKEDIN_FILENAME))

    def test_load_linkedin_raises_clear_error_when_pdf_is_invalid(self):
        (self.data_dir / LINKEDIN_FILENAME).write_bytes(b"not-a-real-pdf")

        with patch(
            "src.app.infrastructure.content.resource_loader.PdfReader",
            side_effect=Exception("bad pdf"),
        ):
            with self.assertRaises(InvalidContentError) as context:
                self.loader.load_linkedin()

        self.assertIn("Invalid PDF resource file", str(context.exception))
        self.assertIn(str(self.data_dir / LINKEDIN_FILENAME), str(context.exception))

    def test_load_prompt_resources_uses_configured_data_directory(self):
        resources = self.loader.load_prompt_resources()

        self.assertEqual(resources.summary, "Summary")
        self.assertEqual(resources.style, "Style")
        self.assertEqual(resources.facts["name"], "Tumelo")
        self.assertEqual(resources.linkedin, LINKEDIN_NOT_AVAILABLE)

    def test_build_prompt_context_uses_loaded_resources(self):
        context = self.loader.build_prompt_context(now=datetime(2026, 5, 28, 9, 30, 0))

        self.assertEqual(context["name"], "Tumelo")
        self.assertEqual(context["full_name"], "Tumelo Tshana Konaite")
        self.assertEqual(context["summary"], "Summary")
        self.assertEqual(context["style"], "Style")
        self.assertEqual(context["linkedin"], LINKEDIN_NOT_AVAILABLE)
        self.assertIn("tumelo@example.com", context["contact_links"])
        self.assertIn("https://linkedin.com/in/tumelo", context["contact_links"])
        self.assertIn("https://github.com/tumelo", context["contact_links"])
        self.assertEqual(context["current_datetime"], "2026-05-28 09:30:00")
