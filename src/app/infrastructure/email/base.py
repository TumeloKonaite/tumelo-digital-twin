from __future__ import annotations

from typing import Protocol

from src.app.domain.contact.models import ContactSubmission


class EmailDeliveryError(Exception):
    """Raised when an email cannot be delivered."""


class EmailSender(Protocol):
    def send_contact_request(self, submission: ContactSubmission) -> None:
        """Send a contact request notification."""
