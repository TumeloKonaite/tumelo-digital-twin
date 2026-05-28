from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Request

from src.app.core.config import Settings, get_settings as load_settings
from src.app.domain.twin.prompt_builder import TwinPromptBuilder
from src.app.domain.twin.service import ConversationStore, TwinResourceLoaders, TwinService
from src.app.infrastructure.llm import OpenAIClient


def build_llm_client(settings: Settings) -> OpenAIClient:
    return OpenAIClient(settings=settings)


def build_conversation_store(settings: Settings) -> ConversationStore:
    return ConversationStore(storage_dir=settings.conversation_storage_dir)


def build_resource_loaders(settings: Settings) -> TwinResourceLoaders:
    fallback_prompt_path = settings.content_data_dir.parent / "me.txt"

    def load_prompt_context() -> dict[str, str]:
        from backend.context import build_prompt_context

        return build_prompt_context(data_dir=settings.content_data_dir)

    def load_fallback_personality() -> str:
        return Path(fallback_prompt_path).read_text(encoding="utf-8")

    return TwinResourceLoaders(
        prompt_context=load_prompt_context,
        fallback_personality=load_fallback_personality,
    )


def build_prompt_builder() -> TwinPromptBuilder:
    return TwinPromptBuilder()


def build_twin_service(
    settings: Settings,
    llm_client: OpenAIClient,
    conversation_store: ConversationStore,
    resource_loaders: TwinResourceLoaders,
    prompt_builder: TwinPromptBuilder,
) -> TwinService:
    return TwinService(
        settings=settings,
        llm_client=llm_client,
        conversation_store=conversation_store,
        resource_loaders=resource_loaders,
        prompt_builder=prompt_builder,
    )


def initialize_dependencies(app: FastAPI, settings: Settings | None = None) -> None:
    runtime_settings = settings or load_settings()
    llm_client = build_llm_client(runtime_settings)
    conversation_store = build_conversation_store(runtime_settings)
    resource_loaders = build_resource_loaders(runtime_settings)
    prompt_builder = build_prompt_builder()
    twin_service = build_twin_service(
        settings=runtime_settings,
        llm_client=llm_client,
        conversation_store=conversation_store,
        resource_loaders=resource_loaders,
        prompt_builder=prompt_builder,
    )

    app.state.settings = runtime_settings
    app.state.llm_client = llm_client
    app.state.conversation_store = conversation_store
    app.state.resource_loaders = resource_loaders
    app.state.prompt_builder = prompt_builder
    app.state.twin_service = twin_service


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


def get_llm_client(request: Request) -> OpenAIClient:
    return request.app.state.llm_client


def get_conversation_store(request: Request) -> ConversationStore:
    return request.app.state.conversation_store


def get_resource_loaders(request: Request) -> TwinResourceLoaders:
    return request.app.state.resource_loaders


def get_prompt_builder(request: Request) -> TwinPromptBuilder:
    return request.app.state.prompt_builder


def get_twin_service(request: Request) -> TwinService:
    return request.app.state.twin_service
