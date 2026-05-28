import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

from fastapi.testclient import TestClient


os.environ.setdefault("OPENAI_API_KEY", "test-key")

from src.app.core.config import Settings
from src.app.domain.twin.service import ChatResult, TwinService
from src.app.main import create_app


class ApiTestCase(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.memory_dir = Path(self.temp_dir.name)
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        self.settings = Settings(
            openai_api_key="test-key",
            conversation_storage_dir=self.memory_dir,
        )
        self.app = create_app(settings=self.settings)
        self.client = TestClient(self.app)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_health_endpoint(self):
        response = self.client.get("/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "healthy"})

    def test_chat_endpoint(self):
        create_mock = Mock(
            return_value=Mock(
                choices=[
                    Mock(
                        message=Mock(content="Mocked assistant reply"),
                    )
                ]
            )
        )
        client_mock = Mock()
        client_mock.chat.completions.create = create_mock
        self.app.state.twin_service = TwinService(
            settings=self.settings,
            client=client_mock,
            personality="Test personality",
        )

        response = self.client.post("/chat", json={"message": "Hello there"})

        self.assertEqual(response.status_code, 200)

        payload = response.json()
        self.assertEqual(payload["response"], "Mocked assistant reply")
        self.assertTrue(payload["session_id"])

        create_mock.assert_called_once()
        request_messages = create_mock.call_args.kwargs["messages"]
        self.assertEqual(request_messages[-1], {"role": "user", "content": "Hello there"})

        memory_file = self.memory_dir / f"{payload['session_id']}.json"
        self.assertTrue(memory_file.exists())

    def test_chat_endpoint_delegates_to_twin_service(self):
        service = Mock()
        service.chat.return_value = ChatResult(
            response="Delegated assistant reply",
            session_id="session-123",
        )
        self.app.state.twin_service = service

        response = self.client.post("/chat", json={"message": "Hello there"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {"response": "Delegated assistant reply", "session_id": "session-123"},
        )
        service.chat.assert_called_once_with("Hello there", None)
