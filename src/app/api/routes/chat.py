import json
import os
import uuid
from pathlib import Path
from typing import Iterator

from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from openai import OpenAI

from src.app.api.schemas.chat import ChatRequest, ChatResponse


router = APIRouter()

BACKEND_DIR = Path(__file__).resolve().parents[4] / "backend"
PROJECT_ROOT = BACKEND_DIR.parent

load_dotenv(BACKEND_DIR / ".env", override=True)

client = OpenAI()


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


MEMORY_DIR = resolve_memory_dir()
MEMORY_DIR.mkdir(parents=True, exist_ok=True)


def load_personality() -> str:
    try:
        from backend.context import prompt as build_prompt

        return build_prompt().strip()
    except Exception:
        with open(BACKEND_DIR / "me.txt", "r", encoding="utf-8") as file:
            return file.read().strip()


PERSONALITY = load_personality()


def load_conversation(session_id: str) -> list[dict]:
    file_path = MEMORY_DIR / f"{session_id}.json"
    if file_path.exists():
        with open(file_path, "r", encoding="utf-8") as file:
            return json.load(file)
    return []


def save_conversation(session_id: str, messages: list[dict]) -> None:
    file_path = MEMORY_DIR / f"{session_id}.json"
    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(messages, file, indent=2, ensure_ascii=False)


def build_messages(conversation: list[dict], user_message: str) -> list[dict]:
    messages = [{"role": "system", "content": PERSONALITY}]
    messages.extend(conversation)
    messages.append({"role": "user", "content": user_message})
    return messages


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        session_id = request.session_id or str(uuid.uuid4())
        conversation = load_conversation(session_id)
        messages = build_messages(conversation, request.message)

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
        )

        assistant_response = response.choices[0].message.content
        conversation.append({"role": "user", "content": request.message})
        conversation.append({"role": "assistant", "content": assistant_response})
        save_conversation(session_id, conversation)

        return ChatResponse(response=assistant_response, session_id=session_id)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    try:
        session_id = request.session_id or str(uuid.uuid4())
        conversation = load_conversation(session_id)
        messages = build_messages(conversation, request.message)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    def generate() -> Iterator[str]:
        assistant_parts: list[str] = []
        try:
            stream = client.chat.completions.create(
                model="gpt-4o-mini",
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
                conversation.append({"role": "user", "content": request.message})
                conversation.append({"role": "assistant", "content": assistant_response})
                save_conversation(session_id, conversation)

    return StreamingResponse(
        generate(),
        media_type="text/plain; charset=utf-8",
        headers={"X-Session-Id": session_id},
    )


@router.get("/sessions")
async def list_sessions():
    sessions = []
    for file_path in MEMORY_DIR.glob("*.json"):
        session_id = file_path.stem
        with open(file_path, "r", encoding="utf-8") as file:
            conversation = json.load(file)
            sessions.append(
                {
                    "session_id": session_id,
                    "message_count": len(conversation),
                    "last_message": conversation[-1]["content"] if conversation else None,
                }
            )
    return {"sessions": sessions}
