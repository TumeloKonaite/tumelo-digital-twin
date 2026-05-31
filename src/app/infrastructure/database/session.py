from __future__ import annotations

import os
from pathlib import Path

from dotenv import dotenv_values
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

ENV_FILE_PATH = Path(__file__).resolve().parents[4] / ".env"


def normalize_database_url(database_url: str) -> str:
    if database_url.startswith("postgresql+psycopg://"):
        return database_url
    if database_url.startswith("postgresql://"):
        return database_url.replace("postgresql://", "postgresql+psycopg://", 1)
    if database_url.startswith("postgres://"):
        return database_url.replace("postgres://", "postgresql+psycopg://", 1)
    return database_url


def get_database_url(database_url: str | None = None) -> str:
    resolved_database_url = database_url or os.getenv("DATABASE_URL")
    if not resolved_database_url and ENV_FILE_PATH.exists():
        resolved_database_url = dotenv_values(ENV_FILE_PATH).get("DATABASE_URL")
    if not resolved_database_url:
        raise RuntimeError("DATABASE_URL is not configured.")
    return normalize_database_url(resolved_database_url)


def create_database_engine(database_url: str | None = None) -> Engine:
    return create_engine(
        get_database_url(database_url),
        pool_pre_ping=True,
    )


def create_session_factory(
    database_url: str | None = None,
    *,
    engine: Engine | None = None,
) -> sessionmaker[Session]:
    bound_engine = engine or create_database_engine(database_url)
    return sessionmaker(
        bind=bound_engine,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
        class_=Session,
    )
