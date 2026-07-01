from __future__ import annotations

import logging
from dataclasses import dataclass

from fastapi import FastAPI, Request
from sqlalchemy import Engine
from sqlalchemy.orm import Session, sessionmaker

from src.app.core.config import Settings
from src.app.core.config import get_settings as load_settings
from src.app.domain.contact import ContactRepository, ContactService
from src.app.domain.twin.prompt_builder import TwinPromptBuilder
from src.app.domain.twin.service import LLMAdapter, TwinResourceLoaders, TwinService
from src.app.infrastructure.contact import (
    NullContactRepository,
    PostgresContactRepository,
)
from src.app.infrastructure.content import FactsLoader, ResourceLoader
from src.app.infrastructure.database import (
    create_database_engine,
    create_session_factory,
)
from src.app.infrastructure.email import EmailSender, SMTPEmailSender
from src.app.infrastructure.llm import OpenAIClient, UnavailableLLMClient
from src.app.infrastructure.storage import ConversationStore, FileConversationStore

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class AppDependencies:
    settings: Settings
    llm_client: LLMAdapter
    conversation_store: ConversationStore
    email_sender: EmailSender
    database_engine: Engine | None
    session_factory: sessionmaker[Session] | None
    contact_repository: ContactRepository
    contact_service: ContactService
    facts_loader: FactsLoader
    content_loader: ResourceLoader
    resource_loaders: TwinResourceLoaders
    prompt_builder: TwinPromptBuilder
    twin_service: TwinService


def build_llm_client(settings: Settings) -> LLMAdapter:
    if not settings.openai_api_key:
        logger.warning(
            "OPENAI_API_KEY is not configured; chat completions are unavailable."
        )
        return UnavailableLLMClient()
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
        timeout_seconds=settings.smtp_timeout_seconds,
    )


def build_database_engine(settings: Settings) -> Engine | None:
    if not settings.database_url:
        return None
    return create_database_engine(settings.database_url)


def build_session_factory(
    engine: Engine | None,
) -> sessionmaker[Session] | None:
    if engine is None:
        return None
    return create_session_factory(engine=engine)


def build_contact_repository(
    session_factory: sessionmaker[Session] | None,
) -> ContactRepository:
    if session_factory is None:
        logger.warning(
            "DATABASE_URL is not configured; contact submissions will not be persisted."
        )
        return NullContactRepository()

    return PostgresContactRepository(session_factory=session_factory)


def build_contact_service(
    email_sender: EmailSender,
    repository: ContactRepository,
) -> ContactService:
    return ContactService(
        email_sender=email_sender,
        repository=repository,
    )


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
    llm_client: LLMAdapter,
    conversation_store: ConversationStore,
    contact_service: ContactService,
    resource_loaders: TwinResourceLoaders,
    prompt_builder: TwinPromptBuilder,
) -> TwinService:
    return TwinService(
        settings=settings,
        llm_client=llm_client,
        conversation_store=conversation_store,
        contact_service=contact_service,
        resource_loaders=resource_loaders,
        prompt_builder=prompt_builder,
    )


def build_dependencies(settings: Settings) -> AppDependencies:
    database_engine = build_database_engine(settings)
    session_factory = build_session_factory(database_engine)
    llm_client = build_llm_client(settings)
    conversation_store = build_conversation_store(settings)
    email_sender = build_email_sender(settings)
    contact_repository = build_contact_repository(session_factory)
    contact_service = build_contact_service(email_sender, contact_repository)
    facts_loader = build_facts_loader(settings)
    content_loader = build_content_loader(settings, facts_loader=facts_loader)
    resource_loaders = build_resource_loaders(content_loader)
    prompt_builder = build_prompt_builder()
    twin_service = build_twin_service(
        settings=settings,
        llm_client=llm_client,
        conversation_store=conversation_store,
        contact_service=contact_service,
        resource_loaders=resource_loaders,
        prompt_builder=prompt_builder,
    )

    return AppDependencies(
        settings=settings,
        llm_client=llm_client,
        conversation_store=conversation_store,
        email_sender=email_sender,
        database_engine=database_engine,
        session_factory=session_factory,
        contact_repository=contact_repository,
        contact_service=contact_service,
        facts_loader=facts_loader,
        content_loader=content_loader,
        resource_loaders=resource_loaders,
        prompt_builder=prompt_builder,
        twin_service=twin_service,
    )


def initialize_dependencies(
    app: FastAPI,
    settings: Settings | None = None,
) -> AppDependencies:
    runtime_settings = settings or load_settings()
    dependencies = build_dependencies(runtime_settings)

    app.state.dependencies = dependencies
    return dependencies


def shutdown_dependencies(app: FastAPI) -> None:
    dependencies = getattr(app.state, "dependencies", None)
    if dependencies is None or dependencies.database_engine is None:
        return
    dependencies.database_engine.dispose()


def get_dependencies(request: Request) -> AppDependencies:
    return request.app.state.dependencies


def get_settings(request: Request) -> Settings:
    return get_dependencies(request).settings


def get_llm_client(request: Request) -> LLMAdapter:
    return get_dependencies(request).llm_client


def get_conversation_store(request: Request) -> ConversationStore:
    return get_dependencies(request).conversation_store


def get_email_sender(request: Request) -> EmailSender:
    return get_dependencies(request).email_sender


def get_contact_repository(request: Request) -> ContactRepository:
    return get_dependencies(request).contact_repository


def get_contact_service(request: Request) -> ContactService:
    return get_dependencies(request).contact_service


def get_resource_loaders(request: Request) -> TwinResourceLoaders:
    return get_dependencies(request).resource_loaders


def get_prompt_builder(request: Request) -> TwinPromptBuilder:
    return get_dependencies(request).prompt_builder


def get_twin_service(request: Request) -> TwinService:
    return get_dependencies(request).twin_service
