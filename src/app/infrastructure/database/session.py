from __future__ import annotations

import os

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker


def get_database_url(database_url: str | None = None) -> str:
    resolved_database_url = database_url or os.getenv("DATABASE_URL")
    if not resolved_database_url:
        raise RuntimeError("DATABASE_URL is not configured.")
    return resolved_database_url


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
