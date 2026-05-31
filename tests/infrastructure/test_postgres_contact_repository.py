from __future__ import annotations

from pathlib import Path

from src.app.domain.contact import ContactSubmission
from src.app.infrastructure.contact import PostgresContactRepository
from src.app.infrastructure.database import (
    Base,
    create_database_engine,
    create_session_factory,
)
from src.app.infrastructure.database.models import (
    ContactSubmission as ContactSubmissionModel,
)


def _build_repository(tmp_path: Path) -> tuple[PostgresContactRepository, str]:
    database_url = f"sqlite+pysqlite:///{tmp_path / 'contact_repository.db'}"
    engine = create_database_engine(database_url)
    Base.metadata.create_all(engine)
    session_factory = create_session_factory(engine=engine)
    return PostgresContactRepository(session_factory=session_factory), database_url


def _submission() -> ContactSubmission:
    return ContactSubmission(
        first_name="Jane",
        last_name="Doe",
        email="jane@example.com",
        phone="+27 82 123 4567",
        subject="Interested in working together",
        message="I would like to discuss a role with you.",
    )


def test_create_persists_contact_submission(tmp_path: Path) -> None:
    repository, database_url = _build_repository(tmp_path)

    submission_id = repository.create(_submission())

    session_factory = create_session_factory(database_url)
    with session_factory() as session:
        record = session.get(ContactSubmissionModel, submission_id)

    assert record is not None
    assert record.first_name == "Jane"
    assert record.last_name == "Doe"
    assert record.email == "jane@example.com"
    assert record.phone == "+27 82 123 4567"
    assert record.subject == "Interested in working together"
    assert record.message == "I would like to discuss a role with you."
    assert record.email_status == "pending"
    assert record.email_error is None
    assert record.emailed_at is None


def test_mark_email_sent_updates_delivery_fields(tmp_path: Path) -> None:
    repository, database_url = _build_repository(tmp_path)
    submission_id = repository.create(_submission())
    repository.mark_email_failed(submission_id, "transient smtp failure")

    repository.mark_email_sent(submission_id)

    session_factory = create_session_factory(database_url)
    with session_factory() as session:
        record = session.get(ContactSubmissionModel, submission_id)

    assert record is not None
    assert record.email_status == "sent"
    assert record.emailed_at is not None
    assert record.email_error is None


def test_mark_email_failed_updates_delivery_fields(tmp_path: Path) -> None:
    repository, database_url = _build_repository(tmp_path)
    submission_id = repository.create(_submission())

    repository.mark_email_failed(submission_id, "smtp failure")

    session_factory = create_session_factory(database_url)
    with session_factory() as session:
        record = session.get(ContactSubmissionModel, submission_id)

    assert record is not None
    assert record.email_status == "failed"
    assert record.email_error == "smtp failure"
