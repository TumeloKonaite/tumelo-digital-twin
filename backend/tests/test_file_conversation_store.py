import json
import tempfile
import unittest
from pathlib import Path

from src.app.infrastructure.storage import FileConversationStore


class FileConversationStoreTestCase(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.storage_dir = Path(self.temp_dir.name)
        self.store = FileConversationStore(self.storage_dir)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_load_reads_existing_conversation_history(self):
        session_id = "session-1"
        conversation = [{"role": "assistant", "content": "Earlier context"}]
        (self.storage_dir / f"{session_id}.json").write_text(
            json.dumps(conversation),
            encoding="utf-8",
        )

        result = self.store.load(session_id)

        self.assertEqual(result, conversation)

    def test_save_writes_conversation_history(self):
        session_id = "session-1"
        conversation = [
            {"role": "user", "content": "Hello there"},
            {"role": "assistant", "content": "Mocked reply"},
        ]

        self.store.save(session_id, conversation)

        saved_conversation = json.loads(
            (self.storage_dir / f"{session_id}.json").read_text(encoding="utf-8")
        )
        self.assertEqual(saved_conversation, conversation)

    def test_load_missing_file_returns_empty_history(self):
        self.assertEqual(self.store.load("missing-session"), [])

    def test_load_corrupted_json_returns_empty_history_and_logs_warning(self):
        session_id = "broken-session"
        (self.storage_dir / f"{session_id}.json").write_text("{invalid", encoding="utf-8")

        with self.assertLogs(
            "src.app.infrastructure.storage.file_conversation_store",
            level="WARNING",
        ) as captured_logs:
            result = self.store.load(session_id)

        self.assertEqual(result, [])
        self.assertIn("Falling back to empty history", captured_logs.output[0])

    def test_list_sessions_handles_corrupted_json_gracefully(self):
        valid_session_id = "session-1"
        broken_session_id = "broken-session"
        self.store.save(
            valid_session_id,
            [{"role": "assistant", "content": "Last valid message"}],
        )
        (self.storage_dir / f"{broken_session_id}.json").write_text(
            "{invalid",
            encoding="utf-8",
        )

        sessions = sorted(
            self.store.list_sessions(),
            key=lambda session: session["session_id"],
        )

        self.assertEqual(
            sessions,
            [
                {
                    "session_id": broken_session_id,
                    "message_count": 0,
                    "last_message": None,
                },
                {
                    "session_id": valid_session_id,
                    "message_count": 1,
                    "last_message": "Last valid message",
                },
            ],
        )
