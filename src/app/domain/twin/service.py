from __future__ import annotations

import json
import uuid
from collections.abc import Callable, Iterable, Iterator
from dataclasses import dataclass
from json import JSONDecodeError
from typing import Any, Protocol

from pydantic import Field, ValidationError

from src.app.core.config import Settings
from src.app.domain.contact import (
    ContactService,
    ContactServiceError,
    ContactSubmissionPayload,
)
from src.app.infrastructure.storage import ConversationStore

from .llm_models import (
    LLMCompletion,
    LLMMessage,
    LLMToolCall,
    LLMToolDefinition,
)
from .prompt_builder import TwinPromptBuilder

CONTACT_TOOL_NAME = "submit_contact_request"
CONTACT_TOOL_INSTRUCTIONS = (
    "When a visitor wants to get in touch, collaborate, or discuss an opportunity, "
    "you may help collect their contact details for a formal submission. "
    "Do not invent any values. Collect the required fields naturally: first name, "
    "last name, email, phone, subject, and message. Before submitting, summarize "
    "the collected details and ask for explicit confirmation. Only call the "
    f"`{CONTACT_TOOL_NAME}` tool after the user clearly confirms the submission."
)


@dataclass
class ChatResult:
    response: str
    session_id: str


@dataclass
class StreamingChatResult:
    session_id: str
    stream: Iterator[str]


@dataclass(frozen=True)
class TwinResourceLoaders:
    prompt_context: Callable[[], dict[str, Any]]
    fallback_personality: Callable[[], str]


class ContactToolRequest(ContactSubmissionPayload):
    confirmed_by_user: bool = Field(
        ...,
        description="True only when the user has explicitly confirmed submission.",
    )


class LLMAdapter(Protocol):
    def complete(self, messages: list[LLMMessage]) -> str: ...

    def complete_with_tools(
        self,
        messages: list[LLMMessage],
        tools: list[LLMToolDefinition],
    ) -> LLMCompletion: ...

    def stream_complete(self, messages: list[LLMMessage]) -> Iterator[str]: ...


class TwinService:
    def __init__(
        self,
        settings: Settings,
        llm_client: LLMAdapter,
        conversation_store: ConversationStore,
        prompt_builder: TwinPromptBuilder,
        resource_loaders: TwinResourceLoaders,
        contact_service: ContactService | None = None,
        personality: str | None = None,
    ) -> None:
        self.settings = settings
        self.llm_client = llm_client
        self.conversation_store = conversation_store
        self.prompt_builder = prompt_builder
        self.resource_loaders = resource_loaders
        self.contact_service = contact_service
        self._personality = personality

    @property
    def personality(self) -> str:
        if self._personality is None:
            self._personality = self.load_personality()
        return self._personality

    @personality.setter
    def personality(self, value: str) -> None:
        self._personality = value

    def load_personality(self) -> str:
        try:
            return self.prompt_builder.build_system_prompt(
                **self.resource_loaders.prompt_context()
            ).strip()
        except Exception:
            return self.resource_loaders.fallback_personality().strip()

    @staticmethod
    def generate_session_id() -> str:
        return str(uuid.uuid4())

    def build_messages(
        self,
        conversation: list[dict[str, str]],
        user_message: str,
        *,
        include_tool_instructions: bool = True,
    ) -> list[LLMMessage]:
        messages: list[LLMMessage] = [{"role": "system", "content": self.personality}]
        if include_tool_instructions and self.contact_tool_definitions:
            messages.append({"role": "system", "content": CONTACT_TOOL_INSTRUCTIONS})
        messages.extend(conversation)
        messages.append({"role": "user", "content": user_message})
        return messages

    def chat(self, user_message: str, session_id: str | None = None) -> ChatResult:
        active_session_id = session_id or self.generate_session_id()
        conversation = self.conversation_store.load(active_session_id)
        messages = self.build_messages(
            conversation,
            user_message,
            include_tool_instructions=True,
        )

        assistant_response = self._complete_chat(messages)
        conversation.append({"role": "user", "content": user_message})
        conversation.append({"role": "assistant", "content": assistant_response})
        self.conversation_store.save(active_session_id, conversation)

        return ChatResult(response=assistant_response, session_id=active_session_id)

    def stream_chat(
        self,
        user_message: str,
        session_id: str | None = None,
    ) -> StreamingChatResult:
        active_session_id = session_id or self.generate_session_id()
        conversation = self.conversation_store.load(active_session_id)
        messages = self.build_messages(
            conversation,
            user_message,
            include_tool_instructions=False,
        )
        stream = self.llm_client.stream_complete(messages)

        def generate() -> Iterator[str]:
            assistant_parts: list[str] = []
            try:
                for content in stream:
                    assistant_parts.append(content)
                    yield content
            finally:
                assistant_response = "".join(assistant_parts).strip()
                if assistant_response:
                    conversation.append({"role": "user", "content": user_message})
                    conversation.append(
                        {"role": "assistant", "content": assistant_response}
                    )
                    self.conversation_store.save(active_session_id, conversation)

        return StreamingChatResult(session_id=active_session_id, stream=generate())

    def list_sessions(self) -> list[dict[str, Any]]:
        return self.conversation_store.list_sessions()

    @property
    def contact_tool_definitions(self) -> list[LLMToolDefinition]:
        if self.contact_service is None:
            return []

        schema = ContactToolRequest.model_json_schema()
        return [
            {
                "type": "function",
                "function": {
                    "name": CONTACT_TOOL_NAME,
                    "description": (
                        "Submit a validated contact request after the user has "
                        "explicitly confirmed the final details."
                    ),
                    "parameters": schema,
                },
            }
        ]

    def _complete_chat(self, messages: list[LLMMessage]) -> str:
        if not self.contact_tool_definitions:
            return self.llm_client.complete(messages)

        agent_messages = list(messages)
        for _ in range(3):
            completion = self.llm_client.complete_with_tools(
                agent_messages,
                self.contact_tool_definitions,
            )
            if not completion.tool_calls:
                return completion.content

            agent_messages.append(self._assistant_tool_message(completion))
            agent_messages.extend(self._tool_result_messages(completion.tool_calls))

        raise RuntimeError("Agent exceeded the maximum number of tool rounds.")

    def _assistant_tool_message(self, completion: LLMCompletion) -> LLMMessage:
        return {
            "role": "assistant",
            "content": completion.content,
            "tool_calls": [
                {
                    "id": tool_call.id,
                    "type": "function",
                    "function": {
                        "name": tool_call.name,
                        "arguments": tool_call.arguments,
                    },
                }
                for tool_call in completion.tool_calls
            ],
        }

    def _tool_result_messages(
        self,
        tool_calls: Iterable[LLMToolCall],
    ) -> list[LLMMessage]:
        return [
            {
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": json.dumps(self._execute_tool_call(tool_call)),
            }
            for tool_call in tool_calls
        ]

    def _execute_tool_call(self, tool_call: LLMToolCall) -> dict[str, Any]:
        if tool_call.name != CONTACT_TOOL_NAME:
            return {
                "ok": False,
                "error": f"Unknown tool: {tool_call.name}",
            }

        if self.contact_service is None:
            return {
                "ok": False,
                "error": "Contact submissions are not available right now.",
            }

        try:
            payload = json.loads(tool_call.arguments)
        except JSONDecodeError:
            return {
                "ok": False,
                "error": "The contact submission arguments were not valid JSON.",
            }

        try:
            request = ContactToolRequest.model_validate(payload)
        except ValidationError as exc:
            return {
                "ok": False,
                "error": (
                    "The contact submission is missing required fields or "
                    "contains invalid values."
                ),
                "validation_errors": exc.errors(),
            }

        if not request.confirmed_by_user:
            return {
                "ok": False,
                "error": "Explicit user confirmation is required before submission.",
                "next_action": (
                    "Ask the user to confirm the final details before submitting."
                ),
            }

        try:
            self.contact_service.submit_contact_request(request.to_submission())
        except ContactServiceError:
            return {
                "ok": False,
                "error": "Unable to submit the contact request right now.",
            }

        return {
            "ok": True,
            "message": "Contact request submitted successfully.",
            "submitted_contact": {
                "first_name": request.first_name,
                "last_name": request.last_name,
                "email": request.email,
                "phone": request.phone,
                "subject": request.subject,
                "message": request.message,
            },
        }
