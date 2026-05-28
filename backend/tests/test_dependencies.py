import os
import tempfile
import unittest
from pathlib import Path

from fastapi import Request
from fastapi.testclient import TestClient


os.environ.setdefault("OPENAI_API_KEY", "test-key")

from src.app.core.config import Settings
from src.app.core.dependencies import (
    get_conversation_store,
    get_llm_client,
    get_prompt_builder,
    get_resource_loaders,
    get_settings,
    get_twin_service,
)
from src.app.domain.twin.prompt_builder import TwinPromptBuilder
from src.app.domain.twin.service import ConversationStore, TwinService
from src.app.infrastructure.llm import OpenAIClient
from src.app.main import create_app


class MockTwinService:
    def chat(self, message: str, session_id: str | None):
        return type(
            "Result",
            (),
            {
                "response": f"mocked: {message}",
                "session_id": session_id or "mock-session",
            },
        )()


class DependencyWiringTestCase(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.settings = Settings(
            openai_api_key="test-key",
            conversation_storage_dir=Path(self.temp_dir.name),
        )
        self.app = create_app(settings=self.settings)

    def tearDown(self):
        self.temp_dir.cleanup()

    def _request(self) -> Request:
        return Request(
            {
                "type": "http",
                "app": self.app,
                "headers": [],
                "method": "GET",
                "path": "/",
                "query_string": b"",
                "root_path": "",
                "scheme": "http",
                "client": ("testclient", 50000),
                "server": ("testserver", 80),
                "http_version": "1.1",
            }
        )

    def test_app_initializes_dependency_state(self):
        self.assertIs(self.app.state.settings, self.settings)
        self.assertIsInstance(self.app.state.llm_client, OpenAIClient)
        self.assertIsInstance(self.app.state.conversation_store, ConversationStore)
        self.assertIsInstance(self.app.state.prompt_builder, TwinPromptBuilder)
        self.assertIsInstance(self.app.state.twin_service, TwinService)

    def test_dependency_providers_resolve_from_app_state(self):
        request = self._request()

        self.assertIs(get_settings(request), self.app.state.settings)
        self.assertIs(get_llm_client(request), self.app.state.llm_client)
        self.assertIs(get_conversation_store(request), self.app.state.conversation_store)
        self.assertIs(get_resource_loaders(request), self.app.state.resource_loaders)
        self.assertIs(get_prompt_builder(request), self.app.state.prompt_builder)
        self.assertIs(get_twin_service(request), self.app.state.twin_service)

    def test_chat_route_uses_dependency_override(self):
        self.app.dependency_overrides[get_twin_service] = lambda: MockTwinService()

        response = TestClient(self.app).post("/chat", json={"message": "Hello"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {"response": "mocked: Hello", "session_id": "mock-session"},
        )
        self.app.dependency_overrides.clear()
