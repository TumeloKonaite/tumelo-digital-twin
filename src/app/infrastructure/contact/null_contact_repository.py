from __future__ import annotations

from uuid import UUID, uuid4

from src.app.domain.contact.models import ContactSubmission
from src.app.domain.contact.repository import ContactRepository


class NullContactRepository(ContactRepository):
    """Fallback repository used when database persistence is not configured."""

    def create(self, submission: ContactSubmission) -> UUID:
        return uuid4()

    def mark_email_sent(self, submission_id: UUID) -> None:
        return None

    def mark_email_failed(
        self,
        submission_id: UUID,
        error_message: str | None = None,
    ) -> None:
        return None
