from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.orm import Session, sessionmaker

from src.app.domain.contact.models import ContactSubmission
from src.app.domain.contact.repository import ContactRepository
from src.app.infrastructure.database.models import (
    ContactSubmission as ContactSubmissionModel,
)


class PostgresContactRepository(ContactRepository):
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def create(self, submission: ContactSubmission) -> UUID:
        with self._session_factory.begin() as session:
            record = ContactSubmissionModel(
                first_name=submission.first_name,
                last_name=submission.last_name,
                email=submission.email,
                phone=submission.phone,
                subject=submission.subject,
                message=submission.message,
            )
            session.add(record)
            session.flush()
            return record.id

    def mark_email_sent(self, submission_id: UUID) -> None:
        with self._session_factory.begin() as session:
            record = self._get_submission(session, submission_id)
            record.email_status = "sent"
            record.emailed_at = datetime.now(UTC)
            record.email_error = None

    def mark_email_failed(
        self,
        submission_id: UUID,
        error_message: str | None = None,
    ) -> None:
        with self._session_factory.begin() as session:
            record = self._get_submission(session, submission_id)
            record.email_status = "failed"
            record.email_error = error_message

    def _get_submission(
        self,
        session: Session,
        submission_id: UUID,
    ) -> ContactSubmissionModel:
        record = session.get(ContactSubmissionModel, submission_id)
        if record is None:
            raise ValueError(f"Contact submission {submission_id} was not found.")
        return record
