from __future__ import annotations

import json
import logging
from pathlib import Path

from src.app.infrastructure.storage import FileConversationStore


def test_load_reads_existing_conversation_history(tmp_path: Path) -> None:
    store = FileConversationStore(tmp_path)
    session_id = "session-1"
    conversation = [{"role": "assistant", "content": "Earlier context"}]
    (tmp_path / f"{session_id}.json").write_text(
        json.dumps(conversation),
        encoding="utf-8",
    )

    assert store.load(session_id) == conversation


def test_save_writes_conversation_history(tmp_path: Path) -> None:
    store = FileConversationStore(tmp_path)
    conversation = [
        {"role": "user", "content": "Hello there"},
        {"role": "assistant", "content": "Mocked reply"},
    ]

    store.save("session-1", conversation)

    saved_conversation = json.loads((tmp_path / "session-1.json").read_text(encoding="utf-8"))
    assert saved_conversation == conversation


def test_load_corrupted_json_returns_empty_history_and_logs_warning(
    tmp_path: Path,
    caplog,
) -> None:
    store = FileConversationStore(tmp_path)
    (tmp_path / "broken-session.json").write_text("{invalid", encoding="utf-8")

    with caplog.at_level(
        logging.WARNING,
        logger="src.app.infrastructure.storage.file_conversation_store",
    ):
        result = store.load("broken-session")

    assert result == []
    assert "Falling back to empty history" in caplog.text


def test_list_sessions_handles_invalid_json_gracefully(tmp_path: Path) -> None:
    store = FileConversationStore(tmp_path)
    store.save(
        "session-1",
        [{"role": "assistant", "content": "Last valid message"}],
    )
    (tmp_path / "broken-session.json").write_text("{invalid", encoding="utf-8")

    sessions = sorted(store.list_sessions(), key=lambda session: session["session_id"])

    assert sessions == [
        {
            "session_id": "broken-session",
            "message_count": 0,
            "last_message": None,
        },
        {
            "session_id": "session-1",
            "message_count": 1,
            "last_message": "Last valid message",
        },
    ]
