import json
import os
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator

from dotenv import load_dotenv
from openai import OpenAI

from .prompt_builder import TwinPromptBuilder


BACKEND_DIR = Path(__file__).resolve().parents[4] / "backend"
PROJECT_ROOT = BACKEND_DIR.parent

load_dotenv(BACKEND_DIR / ".env", override=True)


@dataclass
class ChatResult:
    response: str
    session_id: str


@dataclass
class StreamingChatResult:
    session_id: str
    stream: Iterator[str]


class TwinService:
    def __init__(
        self,
        client: Any | None = None,
        memory_dir: Path | None = None,
        personality: str | None = None,
        prompt_builder: TwinPromptBuilder | None = None,
        model: str = "gpt-4o-mini",
    ) -> None:
        self.client = client or OpenAI()
        self.memory_dir = Path(memory_dir) if memory_dir is not None else self.resolve_memory_dir()
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        self.prompt_builder = prompt_builder or TwinPromptBuilder()
        self.personality = personality if personality is not None else self.load_personality()
        self.model = model

    @staticmethod
    def resolve_memory_dir() -> Path:
        env_memory_dir = os.getenv("MEMORY_DIR")
        if env_memory_dir:
            memory_dir = Path(env_memory_dir).expanduser()
            if not memory_dir.is_absolute():
                memory_dir = (PROJECT_ROOT / memory_dir).resolve()
            return memory_dir

        persistent_storage_root = Path("/persistent-storage")
        if persistent_storage_root.exists():
            return persistent_storage_root / "memory"

        return PROJECT_ROOT / "memory"

    def load_personality(self) -> str:
        try:
            from backend.context import build_prompt_context

            return self.prompt_builder.build_system_prompt(**build_prompt_context()).strip()
        except Exception:
            with open(BACKEND_DIR / "me.txt", "r", encoding="utf-8") as file:
                return file.read().strip()

    @staticmethod
    def generate_session_id() -> str:
        return str(uuid.uuid4())

    def load_conversation(self, session_id: str) -> list[dict[str, str]]:
        file_path = self.memory_dir / f"{session_id}.json"
        if file_path.exists():
            with open(file_path, "r", encoding="utf-8") as file:
                return json.load(file)
        return []

    def save_conversation(self, session_id: str, messages: list[dict[str, str]]) -> None:
        file_path = self.memory_dir / f"{session_id}.json"
        with open(file_path, "w", encoding="utf-8") as file:
            json.dump(messages, file, indent=2, ensure_ascii=False)

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
        sessions = []
        for file_path in self.memory_dir.glob("*.json"):
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
