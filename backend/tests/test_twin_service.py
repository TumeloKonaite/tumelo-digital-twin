import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock


os.environ.setdefault("OPENAI_API_KEY", "test-key")

from src.app.core.config import Settings
from src.app.domain.twin.prompt_builder import TwinPromptBuilder
from src.app.domain.twin.service import TwinResourceLoaders, TwinService
from src.app.infrastructure.storage import ConversationStore


class TwinServiceTestCase(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.memory_dir = Path(self.temp_dir.name)
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        self.settings = Settings(
            openai_api_key="test-key",
            conversation_storage_dir=self.memory_dir,
        )
        self.conversation_store = Mock(spec=ConversationStore)
        self.resource_loaders = TwinResourceLoaders(
            prompt_context=lambda: {},
            fallback_personality=lambda: "Fallback personality",
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_chat_loads_context_calls_llm_persists_and_returns_response(self):
        session_id = "session-1"
        self.conversation_store.load.return_value = [
            {"role": "assistant", "content": "Earlier context"}
        ]

        llm_client = Mock()
        llm_client.complete.return_value = "Mocked assistant reply"

        service = TwinService(
            settings=self.settings,
            llm_client=llm_client,
            conversation_store=self.conversation_store,
            prompt_builder=TwinPromptBuilder(),
            resource_loaders=self.resource_loaders,
            personality="Test personality",
        )

        result = service.chat("Hello there", session_id)

        self.assertEqual(result.response, "Mocked assistant reply")
        self.assertEqual(result.session_id, session_id)
        self.conversation_store.load.assert_called_once_with(session_id)
        llm_client.complete.assert_called_once_with(
            [
                {"role": "system", "content": "Test personality"},
                {"role": "assistant", "content": "Earlier context"},
                {"role": "user", "content": "Hello there"},
            ]
        )
        self.conversation_store.save.assert_called_once_with(
            session_id,
            [
                {"role": "assistant", "content": "Earlier context"},
                {"role": "user", "content": "Hello there"},
                {"role": "assistant", "content": "Mocked assistant reply"},
            ],
        )

    def test_stream_chat_persists_conversation_after_stream_completion(self):
        session_id = "stream-session"
        self.conversation_store.load.return_value = []

        llm_client = Mock()
        llm_client.stream_complete.return_value = iter(["Mocked ", "stream"])

        service = TwinService(
            settings=self.settings,
            llm_client=llm_client,
            conversation_store=self.conversation_store,
            prompt_builder=TwinPromptBuilder(),
            resource_loaders=self.resource_loaders,
            personality="Test personality",
        )

        result = service.stream_chat("Hello there", session_id)
        chunks = list(result.stream)

        self.assertEqual(result.session_id, session_id)
        self.assertEqual(chunks, ["Mocked ", "stream"])
        self.conversation_store.load.assert_called_once_with(session_id)
        llm_client.stream_complete.assert_called_once_with(
            [
                {"role": "system", "content": "Test personality"},
                {"role": "user", "content": "Hello there"},
            ]
        )
        self.conversation_store.save.assert_called_once_with(
            session_id,
            [
                {"role": "user", "content": "Hello there"},
                {"role": "assistant", "content": "Mocked stream"},
            ],
        )

    def test_load_personality_uses_prompt_builder(self):
        prompt_builder = Mock(spec=TwinPromptBuilder)
        prompt_builder.build_system_prompt.return_value = "Built prompt   "
        llm_client = Mock()
        prompt_context_loader = Mock(
            return_value={
                "full_name": "Tumelo M",
                "name": "Tumelo",
                "style_heading": "Style guidelines:",
            }
        )
        resource_loaders = TwinResourceLoaders(
            prompt_context=prompt_context_loader,
            fallback_personality=Mock(return_value="Fallback personality"),
        )

        service = TwinService(
            settings=self.settings,
            llm_client=llm_client,
            conversation_store=self.conversation_store,
            prompt_builder=prompt_builder,
            resource_loaders=resource_loaders,
        )

        self.assertEqual(service.personality, "Built prompt")
        prompt_context_loader.assert_called_once_with()
        prompt_builder.build_system_prompt.assert_called_once()
        self.assertEqual(
            prompt_builder.build_system_prompt.call_args.kwargs,
            {
                "full_name": "Tumelo M",
                "name": "Tumelo",
                "style_heading": "Style guidelines:",
            },
        )
    def test_personality_loading_is_lazy_until_needed(self):
        prompt_builder = Mock(spec=TwinPromptBuilder)
        prompt_context_loader = Mock(return_value={"name": "Tumelo", "full_name": "Tumelo M"})
        resource_loaders = TwinResourceLoaders(
            prompt_context=prompt_context_loader,
            fallback_personality=Mock(return_value="Fallback personality"),
        )

        service = TwinService(
            settings=self.settings,
            llm_client=Mock(),
            conversation_store=self.conversation_store,
            prompt_builder=prompt_builder,
            resource_loaders=resource_loaders,
        )

        prompt_context_loader.assert_not_called()
        prompt_builder.build_system_prompt.assert_not_called()
        service.build_messages([], "Hello there")
        prompt_context_loader.assert_called_once_with()
        prompt_builder.build_system_prompt.assert_called_once_with(
            name="Tumelo",
            full_name="Tumelo M",
        )

    def test_list_sessions_delegates_to_conversation_store(self):
        self.conversation_store.list_sessions.return_value = [
            {
                "session_id": "session-1",
                "message_count": 2,
                "last_message": "Latest reply",
            }
        ]

        service = TwinService(
            settings=self.settings,
            llm_client=Mock(),
            conversation_store=self.conversation_store,
            prompt_builder=TwinPromptBuilder(),
            resource_loaders=self.resource_loaders,
            personality="Test personality",
        )

        sessions = service.list_sessions()

        self.assertEqual(
            sessions,
            [
                {
                    "session_id": "session-1",
                    "message_count": 2,
                    "last_message": "Latest reply",
                }
            ],
        )
        self.conversation_store.list_sessions.assert_called_once_with()
