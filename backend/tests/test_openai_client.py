import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from httpx import Request
from openai import APITimeoutError, OpenAI


os.environ.setdefault("OPENAI_API_KEY", "test-key")

from src.app.core.config import Settings
from src.app.infrastructure.llm import OpenAIClient


class OpenAIClientTestCase(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.settings = Settings(
            openai_api_key="test-key",
            openai_model="gpt-4.1-mini",
            openai_timeout_seconds=12.5,
            openai_max_retries=4,
            conversation_storage_dir=Path(self.temp_dir.name),
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_complete_returns_message_content(self):
        sdk_client = Mock()
        sdk_client.chat.completions.create.return_value = Mock(
            choices=[Mock(message=Mock(content="Mocked assistant reply"))]
        )
        client = OpenAIClient(settings=self.settings, client=sdk_client)

        result = client.complete([{"role": "user", "content": "Hello"}])

        self.assertEqual(result, "Mocked assistant reply")
        sdk_client.chat.completions.create.assert_called_once_with(
            model="gpt-4.1-mini",
            messages=[{"role": "user", "content": "Hello"}],
        )

    def test_complete_uses_configured_model(self):
        sdk_client = Mock()
        sdk_client.chat.completions.create.return_value = Mock(
            choices=[Mock(message=Mock(content="Configured model reply"))]
        )
        client = OpenAIClient(settings=self.settings, client=sdk_client)

        client.complete([{"role": "user", "content": "Check model"}])

        self.assertEqual(
            sdk_client.chat.completions.create.call_args.kwargs["model"],
            "gpt-4.1-mini",
        )

    def test_complete_converts_sdk_timeout_to_timeout_error(self):
        sdk_client = Mock()
        sdk_client.chat.completions.create.side_effect = APITimeoutError(
            request=Request("POST", "https://api.openai.com/v1/chat/completions")
        )
        client = OpenAIClient(settings=self.settings, client=sdk_client)

        with self.assertRaisesRegex(TimeoutError, "OpenAI request timed out"):
            client.complete([{"role": "user", "content": "Hello"}])

    def test_client_creation_centralizes_timeout_and_retry_configuration(self):
        with patch("src.app.infrastructure.llm.openai_client.OpenAI") as openai_cls:
            sdk_instance = Mock(spec=OpenAI)
            openai_cls.return_value = sdk_instance

            client = OpenAIClient(settings=self.settings)

        self.assertIs(client._client, sdk_instance)
        openai_cls.assert_called_once_with(
            api_key="test-key",
            timeout=12.5,
            max_retries=4,
        )
