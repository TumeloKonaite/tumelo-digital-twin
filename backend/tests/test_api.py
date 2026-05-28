import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

from fastapi.testclient import TestClient


os.environ.setdefault("OPENAI_API_KEY", "test-key")

from src.app.core.dependencies import get_twin_service
from src.app.core.config import Settings
from src.app.domain.twin.prompt_builder import TwinPromptBuilder
from src.app.domain.twin.service import ChatResult, TwinResourceLoaders, TwinService
from src.app.infrastructure.storage import FileConversationStore
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
        self.resource_loaders = TwinResourceLoaders(
            prompt_context=lambda: {},
            fallback_personality=lambda: "Fallback personality",
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_health_endpoint(self):
        response = self.client.get("/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "healthy"})

    def test_chat_endpoint(self):
        llm_client = Mock()
        llm_client.complete.return_value = "Mocked assistant reply"
        self.app.state.twin_service = TwinService(
            settings=self.settings,
            llm_client=llm_client,
            conversation_store=FileConversationStore(self.memory_dir),
            prompt_builder=TwinPromptBuilder(),
            resource_loaders=self.resource_loaders,
            personality="Test personality",
        )

        response = self.client.post("/chat", json={"message": "Hello there"})

        self.assertEqual(response.status_code, 200)

        payload = response.json()
        self.assertEqual(payload["response"], "Mocked assistant reply")
        self.assertTrue(payload["session_id"])

        llm_client.complete.assert_called_once()
        request_messages = llm_client.complete.call_args.args[0]
        self.assertEqual(request_messages[-1], {"role": "user", "content": "Hello there"})

        memory_file = self.memory_dir / f"{payload['session_id']}.json"
        self.assertTrue(memory_file.exists())

    def test_chat_endpoint_delegates_to_twin_service(self):
        service = Mock()
        service.chat.return_value = ChatResult(
            response="Delegated assistant reply",
            session_id="session-123",
        )
        self.app.dependency_overrides[get_twin_service] = lambda: service

        response = self.client.post("/chat", json={"message": "Hello there"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {"response": "Delegated assistant reply", "session_id": "session-123"},
        )
        service.chat.assert_called_once_with("Hello there", None)
        self.app.dependency_overrides.clear()
