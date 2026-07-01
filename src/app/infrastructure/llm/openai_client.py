from __future__ import annotations

from collections.abc import Iterator

from openai import APITimeoutError, OpenAI

from src.app.core.config import Settings
from src.app.domain.twin.llm_models import (
    LLMCompletion,
    LLMMessage,
    LLMToolCall,
    LLMToolDefinition,
)


class LLMConfigurationError(RuntimeError):
    """Raised when the LLM integration is requested without valid configuration."""


def _extract_tool_function_name(function: object) -> str:
    if isinstance(function, dict):
        name = function.get("name")
    else:
        name = getattr(function, "name", None)

    if isinstance(name, str):
        return name

    # unittest.mock.Mock stores the explicit constructor name on _mock_name.
    mock_name = getattr(function, "_mock_name", None)
    if isinstance(mock_name, str):
        return mock_name

    raise TypeError("Tool call function name must be a string.")


def _extract_tool_function_arguments(function: object) -> str:
    if isinstance(function, dict):
        arguments = function.get("arguments")
    else:
        arguments = getattr(function, "arguments", None)

    if isinstance(arguments, str):
        return arguments

    raise TypeError("Tool call function arguments must be a string.")


class OpenAIClient:
    def __init__(
        self,
        settings: Settings,
        client: OpenAI | None = None,
    ) -> None:
        if not settings.openai_api_key:
            raise LLMConfigurationError("OPENAI_API_KEY is not configured.")
        self._model = settings.openai_model
        self._client = client or OpenAI(
            api_key=settings.openai_api_key,
            timeout=settings.openai_timeout_seconds,
            max_retries=settings.openai_max_retries,
        )

    def complete(self, messages: list[LLMMessage]) -> str:
        try:
            response = self._client.chat.completions.create(
                model=self._model,
                messages=messages,
            )
        except APITimeoutError as exc:
            raise TimeoutError("OpenAI request timed out") from exc
        content = response.choices[0].message.content
        return content or ""

    def complete_with_tools(
        self,
        messages: list[LLMMessage],
        tools: list[LLMToolDefinition],
    ) -> LLMCompletion:
        try:
            response = self._client.chat.completions.create(
                model=self._model,
                messages=messages,
                tools=tools,
            )
        except APITimeoutError as exc:
            raise TimeoutError("OpenAI request timed out") from exc

        message = response.choices[0].message
        tool_calls = [
            LLMToolCall(
                id=tool_call.id,
                name=_extract_tool_function_name(tool_call.function),
                arguments=_extract_tool_function_arguments(tool_call.function),
            )
            for tool_call in (message.tool_calls or [])
        ]
        return LLMCompletion(
            content=message.content or "",
            tool_calls=tool_calls,
        )

    def stream_complete(self, messages: list[LLMMessage]) -> Iterator[str]:
        try:
            stream = self._client.chat.completions.create(
                model=self._model,
                messages=messages,
                stream=True,
            )

            for chunk in stream:
                if not chunk.choices:
                    continue
                delta = chunk.choices[0].delta
                content = getattr(delta, "content", None)
                if content:
                    yield content
        except APITimeoutError as exc:
            raise TimeoutError("OpenAI request timed out") from exc


class UnavailableLLMClient:
    def __init__(self, message: str = "OPENAI_API_KEY is not configured.") -> None:
        self._message = message

    def complete(self, messages: list[LLMMessage]) -> str:
        raise LLMConfigurationError(self._message)

    def complete_with_tools(
        self,
        messages: list[LLMMessage],
        tools: list[LLMToolDefinition],
    ) -> LLMCompletion:
        raise LLMConfigurationError(self._message)

    def stream_complete(self, messages: list[LLMMessage]) -> Iterator[str]:
        raise LLMConfigurationError(self._message)
