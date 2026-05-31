from __future__ import annotations

import uuid
from pathlib import Path

import pytest
from alembic.config import Config
from sqlalchemy import inspect, text
from sqlalchemy.engine import Connection
from sqlalchemy.exc import OperationalError

from alembic import command
from src.app.infrastructure.database import create_database_engine, get_database_url

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ALEMBIC_INI_PATH = PROJECT_ROOT / "alembic.ini"
EXPECTED_COLUMNS = [
    "id",
    "first_name",
    "last_name",
    "email",
    "phone",
    "subject",
    "message",
    "email_status",
    "email_error",
    "emailed_at",
    "created_at",
]


@pytest.fixture
def postgresql_database_url() -> str:
    try:
        database_url = get_database_url()
    except RuntimeError:
        pytest.skip("DATABASE_URL is required for Alembic migration tests.")

    engine = create_database_engine(database_url)
    try:
        if engine.dialect.name != "postgresql":
            pytest.skip("Alembic migration tests require a PostgreSQL database.")
    finally:
        engine.dispose()

    return database_url


@pytest.fixture
def alembic_test_connection(
    postgresql_database_url: str,
) -> tuple[Config, Connection, str]:
    schema_name = f"alembic_test_{uuid.uuid4().hex}"
    engine = create_database_engine(postgresql_database_url)

    try:
        with engine.begin() as connection:
            connection.execute(text(f'CREATE SCHEMA "{schema_name}"'))

        connection = engine.connect()
        connection.exec_driver_sql(f'SET search_path TO "{schema_name}"')
        connection.commit()
    except OperationalError:
        engine.dispose()
        pytest.skip(
            "PostgreSQL migration tests require network access to DATABASE_URL."
        )

    config = Config(str(ALEMBIC_INI_PATH))
    config.attributes["connection"] = connection
    config.attributes["schema"] = schema_name

    try:
        yield config, connection, schema_name
    finally:
        connection.close()
        with engine.begin() as cleanup_connection:
            cleanup_connection.execute(
                text(f'DROP SCHEMA IF EXISTS "{schema_name}" CASCADE')
            )
        engine.dispose()


def test_alembic_upgrade_creates_contact_submissions_table(
    alembic_test_connection: tuple[Config, Connection, str],
) -> None:
    config, connection, schema_name = alembic_test_connection

    command.upgrade(config, "head")

    inspector = inspect(connection)
    assert "contact_submissions" in inspector.get_table_names(schema=schema_name)

    columns = inspector.get_columns("contact_submissions", schema=schema_name)
    assert [column["name"] for column in columns] == EXPECTED_COLUMNS

    columns_by_name = {column["name"]: column for column in columns}
    primary_key = inspector.get_pk_constraint("contact_submissions", schema=schema_name)

    assert primary_key["constrained_columns"] == ["id"]
    assert columns_by_name["id"]["type"].__class__.__name__.lower() == "uuid"
    assert columns_by_name["email_status"]["nullable"] is False
    assert "pending" in str(columns_by_name["email_status"]["default"])
    assert columns_by_name["email_error"]["nullable"] is True
    assert columns_by_name["emailed_at"]["nullable"] is True
    assert columns_by_name["created_at"]["nullable"] is False
    assert columns_by_name["created_at"]["default"] is not None


def test_alembic_downgrade_drops_contact_submissions_table(
    alembic_test_connection: tuple[Config, Connection, str],
) -> None:
    config, connection, schema_name = alembic_test_connection

    command.upgrade(config, "head")
    command.downgrade(config, "base")

    inspector = inspect(connection)
    assert "contact_submissions" not in inspector.get_table_names(schema=schema_name)
