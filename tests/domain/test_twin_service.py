from __future__ import annotations

from unittest.mock import Mock

from src.app.domain.twin.prompt_builder import TwinPromptBuilder
from src.app.domain.twin.service import TwinResourceLoaders, TwinService
from src.app.infrastructure.llm import LLMConfigurationError
from src.app.infrastructure.storage import ConversationStore


def test_chat_loads_context_calls_llm_and_persists_history(settings) -> None:
    conversation_store = Mock(spec=ConversationStore)
    conversation_store.load.return_value = [
        {"role": "assistant", "content": "Earlier context"}
    ]
    llm_client = Mock()
    llm_client.complete.return_value = "Mocked assistant reply"

    service = TwinService(
        settings=settings,
        llm_client=llm_client,
        conversation_store=conversation_store,
        prompt_builder=TwinPromptBuilder(),
        resource_loaders=TwinResourceLoaders(
            prompt_context=lambda: {},
            fallback_personality=lambda: "Fallback personality",
        ),
        personality="Test personality",
    )

    result = service.chat("Hello there", "session-1")

    assert result.response == "Mocked assistant reply"
    assert result.session_id == "session-1"
    conversation_store.load.assert_called_once_with("session-1")
    llm_client.complete.assert_called_once_with(
        [
            {"role": "system", "content": "Test personality"},
            {"role": "assistant", "content": "Earlier context"},
            {"role": "user", "content": "Hello there"},
        ]
    )
    conversation_store.save.assert_called_once_with(
        "session-1",
        [
            {"role": "assistant", "content": "Earlier context"},
            {"role": "user", "content": "Hello there"},
            {"role": "assistant", "content": "Mocked assistant reply"},
        ],
    )


def test_stream_chat_persists_history_after_stream_completion(settings) -> None:
    conversation_store = Mock(spec=ConversationStore)
    conversation_store.load.return_value = []
    llm_client = Mock()
    llm_client.stream_complete.return_value = iter(["Mocked ", "stream"])

    service = TwinService(
        settings=settings,
        llm_client=llm_client,
        conversation_store=conversation_store,
        prompt_builder=TwinPromptBuilder(),
        resource_loaders=TwinResourceLoaders(
            prompt_context=lambda: {},
            fallback_personality=lambda: "Fallback personality",
        ),
        personality="Test personality",
    )

    result = service.stream_chat("Hello there", "stream-session")

    assert result.session_id == "stream-session"
    assert list(result.stream) == ["Mocked ", "stream"]
    conversation_store.load.assert_called_once_with("stream-session")
    llm_client.stream_complete.assert_called_once_with(
        [
            {"role": "system", "content": "Test personality"},
            {"role": "user", "content": "Hello there"},
        ]
    )
    conversation_store.save.assert_called_once_with(
        "stream-session",
        [
            {"role": "user", "content": "Hello there"},
            {"role": "assistant", "content": "Mocked stream"},
        ],
    )


def test_personality_is_built_lazily_from_prompt_context(settings) -> None:
    prompt_builder = Mock(spec=TwinPromptBuilder)
    prompt_builder.build_system_prompt.return_value = "Built prompt   "
    prompt_context_loader = Mock(
        return_value={
            "full_name": "Tumelo Tshana Konaite",
            "name": "Tumelo",
            "style_heading": "Style guidelines:",
        }
    )

    service = TwinService(
        settings=settings,
        llm_client=Mock(),
        conversation_store=Mock(spec=ConversationStore),
        prompt_builder=prompt_builder,
        resource_loaders=TwinResourceLoaders(
            prompt_context=prompt_context_loader,
            fallback_personality=Mock(return_value="Fallback personality"),
        ),
    )

    assert prompt_context_loader.call_count == 0
    assert service.personality == "Built prompt"
    prompt_context_loader.assert_called_once_with()
    prompt_builder.build_system_prompt.assert_called_once_with(
        full_name="Tumelo Tshana Konaite",
        name="Tumelo",
        style_heading="Style guidelines:",
    )


def test_personality_falls_back_when_prompt_building_fails(settings) -> None:
    fallback_loader = Mock(return_value="Fallback personality   ")
    prompt_builder = Mock(spec=TwinPromptBuilder)
    prompt_builder.build_system_prompt.side_effect = RuntimeError("broken content")

    service = TwinService(
        settings=settings,
        llm_client=Mock(),
        conversation_store=Mock(spec=ConversationStore),
        prompt_builder=prompt_builder,
        resource_loaders=TwinResourceLoaders(
            prompt_context=Mock(return_value={"name": "Tumelo"}),
            fallback_personality=fallback_loader,
        ),
    )

    assert service.personality == "Fallback personality"
    fallback_loader.assert_called_once_with()


def test_stream_chat_raises_configuration_error_before_streaming(settings) -> None:
    conversation_store = Mock(spec=ConversationStore)
    conversation_store.load.return_value = []
    llm_client = Mock()
    llm_client.stream_complete.side_effect = LLMConfigurationError(
        "OPENAI_API_KEY is not configured."
    )

    service = TwinService(
        settings=settings,
        llm_client=llm_client,
        conversation_store=conversation_store,
        prompt_builder=TwinPromptBuilder(),
        resource_loaders=TwinResourceLoaders(
            prompt_context=lambda: {},
            fallback_personality=lambda: "Fallback personality",
        ),
        personality="Test personality",
    )

    try:
        service.stream_chat("Hello there", "stream-session")
    except LLMConfigurationError as exc:
        assert str(exc) == "OPENAI_API_KEY is not configured."
    else:
        raise AssertionError("Expected LLMConfigurationError to be raised")
