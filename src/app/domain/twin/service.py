import json
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterator

from src.app.core.config import Settings

from .prompt_builder import TwinPromptBuilder


@dataclass
class ChatResult:
    response: str
    session_id: str


@dataclass
class StreamingChatResult:
    session_id: str
    stream: Iterator[str]


class ConversationStore:
    def __init__(self, storage_dir: Path) -> None:
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def load(self, session_id: str) -> list[dict[str, str]]:
        file_path = self.storage_dir / f"{session_id}.json"
        if file_path.exists():
            with open(file_path, "r", encoding="utf-8") as file:
                return json.load(file)
        return []

    def save(self, session_id: str, messages: list[dict[str, str]]) -> None:
        file_path = self.storage_dir / f"{session_id}.json"
        with open(file_path, "w", encoding="utf-8") as file:
            json.dump(messages, file, indent=2, ensure_ascii=False)

    def list_sessions(self) -> list[dict[str, Any]]:
        sessions = []
        for file_path in self.storage_dir.glob("*.json"):
            with open(file_path, "r", encoding="utf-8") as file:
                conversation = json.load(file)
            sessions.append(
                {
                    "session_id": file_path.stem,
                    "message_count": len(conversation),
                    "last_message": conversation[-1]["content"] if conversation else None,
                }
            )
        return sessions


@dataclass(frozen=True)
class TwinResourceLoaders:
    prompt_context: Callable[[], dict[str, Any]]
    fallback_personality: Callable[[], str]


class TwinService:
    def __init__(
        self,
        settings: Settings,
        client: Any,
        conversation_store: ConversationStore,
        prompt_builder: TwinPromptBuilder,
        resource_loaders: TwinResourceLoaders,
        model: str | None = None,
        personality: str | None = None,
    ) -> None:
        self.settings = settings
        self.client = client
        self.conversation_store = conversation_store
        self.memory_dir = self.conversation_store.storage_dir
        self.prompt_builder = prompt_builder
        self.resource_loaders = resource_loaders
        self.model = model or settings.openai_model
        self.personality = personality if personality is not None else self.load_personality()

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

    def load_conversation(self, session_id: str) -> list[dict[str, str]]:
        return self.conversation_store.load(session_id)

    def save_conversation(self, session_id: str, messages: list[dict[str, str]]) -> None:
        self.conversation_store.save(session_id, messages)

    def build_messages(
        self,
        conversation: list[dict[str, str]],
        user_message: str,
    ) -> list[dict[str, str]]:
        messages = [{"role": "system", "content": self.personality}]
        messages.extend(conversation)
        messages.append({"role": "user", "content": user_message})
        return messages

    def chat(self, user_message: str, session_id: str | None = None) -> ChatResult:
        active_session_id = session_id or self.generate_session_id()
        conversation = self.load_conversation(active_session_id)
        messages = self.build_messages(conversation, user_message)

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
        )

        assistant_response = response.choices[0].message.content
        conversation.append({"role": "user", "content": user_message})
        conversation.append({"role": "assistant", "content": assistant_response})
        self.save_conversation(active_session_id, conversation)

        return ChatResult(response=assistant_response, session_id=active_session_id)

    def stream_chat(
        self,
        user_message: str,
        session_id: str | None = None,
    ) -> StreamingChatResult:
        active_session_id = session_id or self.generate_session_id()
        conversation = self.load_conversation(active_session_id)
        messages = self.build_messages(conversation, user_message)

        def generate() -> Iterator[str]:
            assistant_parts: list[str] = []
            try:
                stream = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    stream=True,
                )

                for chunk in stream:
                    if not chunk.choices:
                        continue
                    delta = chunk.choices[0].delta
                    content = getattr(delta, "content", None)
                    if not content:
                        continue
                    assistant_parts.append(content)
                    yield content
            finally:
                assistant_response = "".join(assistant_parts).strip()
                if assistant_response:
                    conversation.append({"role": "user", "content": user_message})
                    conversation.append({"role": "assistant", "content": assistant_response})
                    self.save_conversation(active_session_id, conversation)

        return StreamingChatResult(session_id=active_session_id, stream=generate())

    def list_sessions(self) -> list[dict[str, Any]]:
        return self.conversation_store.list_sessions()
