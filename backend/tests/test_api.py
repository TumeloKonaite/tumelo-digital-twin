import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from fastapi.testclient import TestClient


os.environ.setdefault("OPENAI_API_KEY", "test-key")

from src.app.main import app
from src.app.api.routes import chat as chat_routes
from src.app.domain.twin.service import ChatResult, TwinService


class ApiTestCase(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.memory_dir = Path(self.temp_dir.name)
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        self.memory_patch = patch.object(chat_routes.twin_service, "memory_dir", self.memory_dir)
        self.memory_patch.start()
        self.client = TestClient(app)

    def tearDown(self):
        self.memory_patch.stop()
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
        service = TwinService(
            client=client_mock,
            memory_dir=self.memory_dir,
            personality="Test personality",
        )

        app.dependency_overrides[chat_routes.get_twin_service] = lambda: service
        try:
            response = self.client.post("/chat", json={"message": "Hello there"})
        finally:
            app.dependency_overrides.clear()

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

        app.dependency_overrides[chat_routes.get_twin_service] = lambda: service
        try:
            response = self.client.post("/chat", json={"message": "Hello there"})
        finally:
            app.dependency_overrides.clear()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {"response": "Delegated assistant reply", "session_id": "session-123"},
        )
        service.chat.assert_called_once_with("Hello there", None)
