from __future__ import annotations

from logging.config import fileConfig
from typing import Any

from sqlalchemy import engine_from_config, pool
from sqlalchemy.engine import Connection

from alembic import context
from src.app.infrastructure.database import Base, get_database_url

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def _get_database_url() -> str:
    configured_url = config.get_main_option("sqlalchemy.url")
    return get_database_url(configured_url or None)


def _get_configure_kwargs() -> dict[str, Any]:
    configure_kwargs: dict[str, Any] = {
        "target_metadata": target_metadata,
        "compare_type": True,
    }
    version_table_schema = config.attributes.get("schema")
    if version_table_schema:
        configure_kwargs["version_table_schema"] = version_table_schema
    return configure_kwargs


def run_migrations_offline() -> None:
    context.configure(
        url=_get_database_url(),
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        **_get_configure_kwargs(),
    )

    with context.begin_transaction():
        context.run_migrations()


def _run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        **_get_configure_kwargs(),
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    existing_connection = config.attributes.get("connection")
    if existing_connection is not None:
        _run_migrations(existing_connection)
        return

    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = _get_database_url()

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        _run_migrations(connection)


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
