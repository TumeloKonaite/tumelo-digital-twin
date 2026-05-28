import json
import tempfile
import unittest
from pathlib import Path

from backend.resources import load_resources
from src.app.core.config import PROJECT_ROOT
from src.app.core.content_paths import resolve_data_dir, resolve_data_path


class ContentPathResolutionTestCase(unittest.TestCase):
    def test_default_data_dir_resolves_to_repo_data_directory(self):
        self.assertEqual(resolve_data_dir(), PROJECT_ROOT / "data")

    def test_custom_data_path_resolves_under_provided_directory(self):
        custom_dir = Path(tempfile.gettempdir()) / "shadow-clone-test-data"

        self.assertEqual(
            resolve_data_path("summary.txt", data_dir=custom_dir),
            custom_dir / "summary.txt",
        )


class ResourceLoadingTestCase(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.data_dir = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def _write_required_files(self) -> None:
        (self.data_dir / "summary.txt").write_text("Summary", encoding="utf-8")
        (self.data_dir / "style.txt").write_text("Style", encoding="utf-8")
        (self.data_dir / "twin_profile.json").write_text(
            json.dumps({"name": "Tumelo", "full_name": "Tumelo Tshana Konaite"}),
            encoding="utf-8",
        )

    def test_load_resources_uses_custom_data_dir(self):
        self._write_required_files()

        resources = load_resources(self.data_dir)

        self.assertEqual(resources.summary, "Summary")
        self.assertEqual(resources.style, "Style")
        self.assertEqual(resources.facts["name"], "Tumelo")
        self.assertEqual(resources.linkedin, "LinkedIn profile not available")

    def test_load_resources_raises_when_required_file_is_missing(self):
        (self.data_dir / "style.txt").write_text("Style", encoding="utf-8")
        (self.data_dir / "twin_profile.json").write_text(
            json.dumps({"name": "Tumelo", "full_name": "Tumelo Tshana Konaite"}),
            encoding="utf-8",
        )

        with self.assertRaises(FileNotFoundError):
            load_resources(self.data_dir)
