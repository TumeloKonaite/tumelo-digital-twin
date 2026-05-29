from __future__ import annotations

from unittest.mock import Mock

import pytest

from src.app.core.dependencies import get_twin_service
from src.app.domain.twin.service import ChatResult, StreamingChatResult


@pytest.fixture
def twin_service_override(app):
    service = Mock()
    app.dependency_overrides[get_twin_service] = lambda: service
    yield service
    app.dependency_overrides.clear()


def test_chat_route_returns_service_response(client, twin_service_override) -> None:
    twin_service_override.chat.return_value = ChatResult(
        response="Mocked assistant reply",
        session_id="session-123",
    )

    response = client.post("/chat", json={"message": "Hello there"})

    assert response.status_code == 200
    assert response.json() == {
        "response": "Mocked assistant reply",
        "session_id": "session-123",
    }
    twin_service_override.chat.assert_called_once_with("Hello there", None)


def test_chat_route_returns_500_when_service_fails(
    client, twin_service_override
) -> None:
    twin_service_override.chat.side_effect = RuntimeError("llm unavailable")

    response = client.post("/chat", json={"message": "Hello there"})

    assert response.status_code == 500
    assert response.json() == {"detail": "llm unavailable"}


def test_chat_stream_route_returns_streamed_response(
    client, twin_service_override
) -> None:
    twin_service_override.stream_chat.return_value = StreamingChatResult(
        session_id="stream-session",
        stream=iter(["Mocked ", "stream"]),
    )

    response = client.post(
        "/chat/stream",
        json={"message": "Hello there", "session_id": "stream-session"},
    )

    assert response.status_code == 200
    assert response.text == "Mocked stream"
    assert response.headers["x-session-id"] == "stream-session"
    assert response.headers["content-type"].startswith("text/plain")
    twin_service_override.stream_chat.assert_called_once_with(
        "Hello there",
        "stream-session",
    )


def test_list_sessions_route_returns_service_sessions(
    client, twin_service_override
) -> None:
    twin_service_override.list_sessions.return_value = [
        {
            "session_id": "session-1",
            "message_count": 2,
            "last_message": "Latest reply",
        }
    ]

    response = client.get("/sessions")

    assert response.status_code == 200
    assert response.json() == {
        "sessions": [
            {
                "session_id": "session-1",
                "message_count": 2,
                "last_message": "Latest reply",
            }
        ]
    }
    twin_service_override.list_sessions.assert_called_once_with()
