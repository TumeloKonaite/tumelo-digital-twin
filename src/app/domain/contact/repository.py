from __future__ import annotations

from typing import Protocol
from uuid import UUID

from .models import ContactSubmission


class ContactRepository(Protocol):
    def create(self, submission: ContactSubmission) -> UUID:
        """Persist a new contact submission and return its identifier."""

    def mark_email_sent(self, submission_id: UUID) -> None:
        """Persist a successful email delivery for a contact submission."""

    def mark_email_failed(
        self,
        submission_id: UUID,
        error_message: str | None = None,
    ) -> None:
        """Persist a failed email delivery for a contact submission."""
