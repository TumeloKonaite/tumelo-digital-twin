from __future__ import annotations

from pathlib import Path

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


def test_create_persists_contact_submission(
    tmp_path: Path,
    contact_submission,
) -> None:
    repository, database_url = _build_repository(tmp_path)

    submission_id = repository.create(contact_submission)

    session_factory = create_session_factory(database_url)
    with session_factory() as session:
        record = session.get(ContactSubmissionModel, submission_id)

    assert record is not None
    assert record.first_name == contact_submission.first_name
    assert record.last_name == contact_submission.last_name
    assert record.email == contact_submission.email
    assert record.phone == contact_submission.phone
    assert record.subject == contact_submission.subject
    assert record.message == contact_submission.message
    assert record.email_status == "pending"
    assert record.email_error is None
    assert record.emailed_at is None


def test_mark_email_sent_updates_delivery_fields(
    tmp_path: Path,
    contact_submission,
) -> None:
    repository, database_url = _build_repository(tmp_path)
    submission_id = repository.create(contact_submission)
    repository.mark_email_failed(submission_id, "transient smtp failure")

    repository.mark_email_sent(submission_id)

    session_factory = create_session_factory(database_url)
    with session_factory() as session:
        record = session.get(ContactSubmissionModel, submission_id)

    assert record is not None
    assert record.email_status == "sent"
    assert record.emailed_at is not None
    assert record.email_error is None


def test_mark_email_failed_updates_delivery_fields(
    tmp_path: Path,
    contact_submission,
) -> None:
    repository, database_url = _build_repository(tmp_path)
    submission_id = repository.create(contact_submission)

    repository.mark_email_failed(submission_id, "smtp failure")

    session_factory = create_session_factory(database_url)
    with session_factory() as session:
        record = session.get(ContactSubmissionModel, submission_id)

    assert record is not None
    assert record.email_status == "failed"
    assert record.email_error == "smtp failure"
