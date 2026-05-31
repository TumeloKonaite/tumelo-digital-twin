from __future__ import annotations

from sqlalchemy.orm import Session

from src.app.infrastructure.database import (
    ContactSubmission,
    create_database_engine,
    create_session_factory,
)


def test_database_models_import_successfully() -> None:
    assert ContactSubmission.__tablename__ == "contact_submissions"


def test_database_engine_can_be_created_from_database_url() -> None:
    database_url = "postgresql+psycopg://user:pass@localhost/test_db"

    engine = create_database_engine(database_url)

    assert engine.url.render_as_string(hide_password=False) == database_url


def test_session_factory_can_be_created_from_database_url() -> None:
    database_url = "postgresql+psycopg://user:pass@localhost/test_db"

    session_factory = create_session_factory(database_url)

    session = session_factory()
    try:
        assert session.bind is not None
        assert isinstance(session, Session)
        assert session.expire_on_commit is False
    finally:
        session.close()


def test_contact_submission_model_has_expected_columns() -> None:
    columns = ContactSubmission.__table__.columns

    assert list(columns.keys()) == [
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
    assert columns["id"].primary_key is True
    assert columns["first_name"].nullable is False
    assert columns["last_name"].nullable is False
    assert columns["email"].nullable is False
    assert columns["phone"].nullable is False
    assert columns["subject"].nullable is False
    assert columns["message"].nullable is False
    assert columns["email_status"].nullable is False
    assert columns["email_status"].default.arg == "pending"
    assert columns["email_error"].nullable is True
    assert columns["emailed_at"].nullable is True
    assert columns["created_at"].nullable is False
    assert columns["created_at"].server_default is not None
