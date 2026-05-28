import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from fastapi.testclient import TestClient
from pydantic import ValidationError


os.environ.setdefault("OPENAI_API_KEY", "test-key")

from src.app.core.config import PROJECT_ROOT, Settings, get_settings
from src.app.main import create_app


class SettingsTestCase(unittest.TestCase):
    def tearDown(self):
        get_settings.cache_clear()

    def test_settings_load_from_environment(self):
        with tempfile.TemporaryDirectory() as temp_dir, patch.dict(
            os.environ,
            {
                "OPENAI_API_KEY": "env-test-key",
                "OPENAI_MODEL": "gpt-4.1-mini",
                "CONTENT_DATA_DIR": "backend/data",
                "CONVERSATION_STORAGE_DIR": temp_dir,
                "CORS_ORIGINS": "http://localhost:3000,http://localhost:5173",
            },
            clear=True,
        ):
            settings = Settings(_env_file=None)

        self.assertEqual(settings.openai_api_key, "env-test-key")
        self.assertEqual(settings.openai_model, "gpt-4.1-mini")
        self.assertEqual(settings.content_data_dir, PROJECT_ROOT / "backend" / "data")
        self.assertEqual(settings.conversation_storage_dir, Path(temp_dir))
        self.assertEqual(
            settings.cors_origins,
            ["http://localhost:3000", "http://localhost:5173"],
        )

    def test_settings_defaults_work(self):
        with patch.dict(
            os.environ,
            {"OPENAI_API_KEY": "env-test-key"},
            clear=True,
        ):
            settings = Settings(_env_file=None)

        self.assertEqual(settings.openai_model, "gpt-4o-mini")
        self.assertEqual(settings.content_data_dir, PROJECT_ROOT / "backend" / "data")
        self.assertEqual(settings.conversation_storage_dir, PROJECT_ROOT / "memory")
        self.assertEqual(settings.cors_origins, ["http://localhost:3000"])

    def test_missing_openai_api_key_raises_validation_error(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ValidationError) as context:
                Settings(_env_file=None)

        self.assertIn("OPENAI_API_KEY", str(context.exception))

    def test_invalid_content_data_dir_raises_validation_error(self):
        with patch.dict(
            os.environ,
            {
                "OPENAI_API_KEY": "env-test-key",
                "CONTENT_DATA_DIR": "backend/missing-data",
            },
            clear=True,
        ):
            with self.assertRaises(ValidationError) as context:
                Settings(_env_file=None)

        self.assertIn("CONTENT_DATA_DIR does not exist", str(context.exception))

    def test_services_can_receive_settings_via_dependency_injection(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            settings = Settings(
                openai_api_key="env-test-key",
                conversation_storage_dir=Path(temp_dir),
            )
            app = create_app(settings=settings)
            create_mock = Mock(
                return_value=Mock(
                    choices=[
                        Mock(
                            message=Mock(content="Injected reply"),
                        )
                    ]
                )
            )
            client_mock = Mock()
            client_mock.chat.completions.create = create_mock
            app.state.twin_service.client = client_mock
            app.state.twin_service.personality = "Injected personality"

            response = TestClient(app).post("/chat", json={"message": "hello"})

        self.assertIs(app.state.settings, settings)
        self.assertIs(app.state.twin_service.settings, settings)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["response"], "Injected reply")
