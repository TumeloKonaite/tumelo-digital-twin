import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch


os.environ.setdefault("OPENAI_API_KEY", "test-key")

from src.app.domain.twin.service import TwinService


class TwinServiceTestCase(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.memory_dir = Path(self.temp_dir.name)
        self.memory_dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_chat_loads_context_calls_llm_persists_and_returns_response(self):
        session_id = "session-1"
        memory_file = self.memory_dir / f"{session_id}.json"
        memory_file.write_text(
            '[{"role":"assistant","content":"Earlier context"}]',
            encoding="utf-8",
        )

        fake_response = Mock(
            choices=[
                Mock(
                    message=Mock(content="Mocked assistant reply"),
                )
            ]
        )
        client_mock = Mock()
        client_mock.chat.completions.create = Mock(return_value=fake_response)

        service = TwinService(
            client=client_mock,
            memory_dir=self.memory_dir,
            personality="Test personality",
        )

        with patch.object(service, "load_conversation", wraps=service.load_conversation) as load_mock, patch.object(
            service,
            "build_messages",
            wraps=service.build_messages,
        ) as build_mock, patch.object(
            service,
            "save_conversation",
            wraps=service.save_conversation,
        ) as save_mock:
            result = service.chat("Hello there", session_id)

        self.assertEqual(result.response, "Mocked assistant reply")
        self.assertEqual(result.session_id, session_id)
        load_mock.assert_called_once_with(session_id)
        build_mock.assert_called_once()
        client_mock.chat.completions.create.assert_called_once_with(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Test personality"},
                {"role": "assistant", "content": "Earlier context"},
                {"role": "user", "content": "Hello there"},
            ],
        )
        save_mock.assert_called_once_with(
            session_id,
            [
                {"role": "assistant", "content": "Earlier context"},
                {"role": "user", "content": "Hello there"},
                {"role": "assistant", "content": "Mocked assistant reply"},
            ],
        )
        self.assertEqual(
            json.loads(memory_file.read_text(encoding="utf-8")),
            [
                {"role": "assistant", "content": "Earlier context"},
                {"role": "user", "content": "Hello there"},
                {"role": "assistant", "content": "Mocked assistant reply"},
            ],
        )

    def test_stream_chat_persists_conversation_after_stream_completion(self):
        session_id = "stream-session"
        memory_file = self.memory_dir / f"{session_id}.json"
        memory_file.write_text("[]", encoding="utf-8")

        stream_chunks = [
            Mock(choices=[Mock(delta=Mock(content="Mocked "))]),
            Mock(choices=[Mock(delta=Mock(content="stream"))]),
        ]
        client_mock = Mock()
        client_mock.chat.completions.create = Mock(return_value=stream_chunks)

        service = TwinService(
            client=client_mock,
            memory_dir=self.memory_dir,
            personality="Test personality",
        )

        with patch.object(service, "load_conversation", wraps=service.load_conversation) as load_mock, patch.object(
            service,
            "build_messages",
            wraps=service.build_messages,
        ) as build_mock, patch.object(
            service,
            "save_conversation",
            wraps=service.save_conversation,
        ) as save_mock:
            result = service.stream_chat("Hello there", session_id)
            chunks = list(result.stream)

        self.assertEqual(result.session_id, session_id)
        self.assertEqual(chunks, ["Mocked ", "stream"])
        load_mock.assert_called_once_with(session_id)
        build_mock.assert_called_once()
        client_mock.chat.completions.create.assert_called_once_with(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Test personality"},
                {"role": "user", "content": "Hello there"},
            ],
            stream=True,
        )
        save_mock.assert_called_once_with(
            session_id,
            [
                {"role": "user", "content": "Hello there"},
                {"role": "assistant", "content": "Mocked stream"},
            ],
        )
        self.assertEqual(
            json.loads(memory_file.read_text(encoding="utf-8")),
            [
                {"role": "user", "content": "Hello there"},
                {"role": "assistant", "content": "Mocked stream"},
            ],
        )
