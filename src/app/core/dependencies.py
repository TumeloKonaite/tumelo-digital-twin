from __future__ import annotations

from fastapi import FastAPI, Request

from src.app.core.config import Settings
from src.app.core.config import get_settings as load_settings
from src.app.domain.contact import ContactService
from src.app.domain.twin.prompt_builder import TwinPromptBuilder
from src.app.domain.twin.service import TwinResourceLoaders, TwinService
from src.app.infrastructure.content import FactsLoader, ResourceLoader
from src.app.infrastructure.email import EmailSender, SMTPEmailSender
from src.app.infrastructure.llm import OpenAIClient
from src.app.infrastructure.storage import ConversationStore, FileConversationStore


def build_llm_client(settings: Settings) -> OpenAIClient:
    return OpenAIClient(settings=settings)


def build_conversation_store(settings: Settings) -> ConversationStore:
    return FileConversationStore(storage_dir=settings.conversation_storage_dir)


def build_email_sender(settings: Settings) -> EmailSender:
    return SMTPEmailSender(
        host=settings.smtp_host,
        port=settings.smtp_port,
        username=settings.smtp_username,
        password=settings.smtp_password,
        from_email=settings.smtp_from_email,
        to_email=settings.contact_to_email,
        use_tls=settings.smtp_use_tls,
    )


def build_contact_service(email_sender: EmailSender) -> ContactService:
    return ContactService(email_sender=email_sender)


def build_facts_loader(settings: Settings) -> FactsLoader:
    return FactsLoader(data_dir=settings.content_data_dir)


def build_content_loader(
    settings: Settings,
    facts_loader: FactsLoader | None = None,
) -> ResourceLoader:
    return ResourceLoader(
        data_dir=settings.content_data_dir,
        facts_loader=facts_loader,
    )


def build_resource_loaders(content_loader: ResourceLoader) -> TwinResourceLoaders:
    return TwinResourceLoaders(
        prompt_context=content_loader.build_prompt_context,
        fallback_personality=content_loader.load_fallback_personality,
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
    email_sender = build_email_sender(runtime_settings)
    contact_service = build_contact_service(email_sender)
    facts_loader = build_facts_loader(runtime_settings)
    content_loader = build_content_loader(runtime_settings, facts_loader=facts_loader)
    resource_loaders = build_resource_loaders(content_loader)
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
    app.state.email_sender = email_sender
    app.state.contact_service = contact_service
    app.state.facts_loader = facts_loader
    app.state.content_loader = content_loader
    app.state.resource_loaders = resource_loaders
    app.state.prompt_builder = prompt_builder
    app.state.twin_service = twin_service


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


def get_llm_client(request: Request) -> OpenAIClient:
    return request.app.state.llm_client


def get_conversation_store(request: Request) -> ConversationStore:
    return request.app.state.conversation_store


def get_email_sender(request: Request) -> EmailSender:
    return request.app.state.email_sender


def get_contact_service(request: Request) -> ContactService:
    return request.app.state.contact_service


def get_resource_loaders(request: Request) -> TwinResourceLoaders:
    return request.app.state.resource_loaders


def get_prompt_builder(request: Request) -> TwinPromptBuilder:
    return request.app.state.prompt_builder


def get_twin_service(request: Request) -> TwinService:
    return request.app.state.twin_service
