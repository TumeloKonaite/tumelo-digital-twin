from __future__ import annotations

from unittest.mock import Mock, patch

from httpx import Request
from openai import APITimeoutError, OpenAI

from src.app.infrastructure.llm import OpenAIClient


def test_complete_returns_message_content(settings) -> None:
    sdk_client = Mock()
    sdk_client.chat.completions.create.return_value = Mock(
        choices=[Mock(message=Mock(content="Mocked assistant reply"))]
    )
    client = OpenAIClient(settings=settings, client=sdk_client)

    result = client.complete([{"role": "user", "content": "Hello"}])

    assert result == "Mocked assistant reply"
    sdk_client.chat.completions.create.assert_called_once_with(
        model=settings.openai_model,
        messages=[{"role": "user", "content": "Hello"}],
    )


def test_complete_converts_sdk_timeout_to_timeout_error(settings) -> None:
    sdk_client = Mock()
    sdk_client.chat.completions.create.side_effect = APITimeoutError(
        request=Request("POST", "https://api.openai.com/v1/chat/completions")
    )
    client = OpenAIClient(settings=settings, client=sdk_client)

    try:
        client.complete([{"role": "user", "content": "Hello"}])
    except TimeoutError as exc:
        assert str(exc) == "OpenAI request timed out"
    else:
        raise AssertionError("Expected TimeoutError to be raised")


def test_complete_with_tools_returns_tool_calls(settings) -> None:
    sdk_client = Mock()
    sdk_client.chat.completions.create.return_value = Mock(
        choices=[
            Mock(
                message=Mock(
                    content="",
                    tool_calls=[
                        Mock(
                            id="tool-call-1",
                            function=Mock(
                                name="submit_contact_request",
                                arguments='{"email":"jane@example.com"}',
                            ),
                        )
                    ],
                )
            )
        ]
    )
    client = OpenAIClient(settings=settings, client=sdk_client)

    result = client.complete_with_tools(
        [{"role": "user", "content": "Help me get in touch"}],
        [
            {
                "type": "function",
                "function": {
                    "name": "submit_contact_request",
                    "parameters": {"type": "object"},
                },
            }
        ],
    )

    assert result.content == ""
    assert len(result.tool_calls) == 1
    assert result.tool_calls[0].id == "tool-call-1"
    assert result.tool_calls[0].name == "submit_contact_request"
    assert result.tool_calls[0].arguments == '{"email":"jane@example.com"}'
    sdk_client.chat.completions.create.assert_called_once_with(
        model=settings.openai_model,
        messages=[{"role": "user", "content": "Help me get in touch"}],
        tools=[
            {
                "type": "function",
                "function": {
                    "name": "submit_contact_request",
                    "parameters": {"type": "object"},
                },
            }
        ],
    )


def test_stream_complete_yields_only_non_empty_chunks(settings) -> None:
    sdk_client = Mock()
    sdk_client.chat.completions.create.return_value = [
        Mock(choices=[]),
        Mock(choices=[Mock(delta=Mock(content="Hello "))]),
        Mock(choices=[Mock(delta=Mock(content=None))]),
        Mock(choices=[Mock(delta=Mock(content="world"))]),
    ]
    client = OpenAIClient(settings=settings, client=sdk_client)

    chunks = list(client.stream_complete([{"role": "user", "content": "Hi"}]))

    assert chunks == ["Hello ", "world"]
    sdk_client.chat.completions.create.assert_called_once_with(
        model=settings.openai_model,
        messages=[{"role": "user", "content": "Hi"}],
        stream=True,
    )


def test_client_creation_centralizes_timeout_and_retry_configuration(settings) -> None:
    with patch("src.app.infrastructure.llm.openai_client.OpenAI") as openai_cls:
        sdk_instance = Mock(spec=OpenAI)
        openai_cls.return_value = sdk_instance

        client = OpenAIClient(settings=settings)

    assert client._client is sdk_instance
    openai_cls.assert_called_once_with(
        api_key="test-key",
        timeout=settings.openai_timeout_seconds,
        max_retries=settings.openai_max_retries,
    )
