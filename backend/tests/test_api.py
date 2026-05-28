import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from fastapi.testclient import TestClient


os.environ.setdefault("OPENAI_API_KEY", "test-key")

from src.app.main import app
from src.app.api.routes import chat as chat_routes


class ApiTestCase(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.memory_dir = Path(self.temp_dir.name)
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        self.memory_patch = patch.object(chat_routes, "MEMORY_DIR", self.memory_dir)
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
        fake_response = SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(content="Mocked assistant reply"),
                )
            ]
        )

        with patch.object(
            chat_routes.client.chat.completions,
            "create",
            return_value=fake_response,
        ) as create_mock:
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
