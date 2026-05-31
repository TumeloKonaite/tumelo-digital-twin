from __future__ import annotations

from src.app.domain.contact.models import ContactSubmission
from src.app.infrastructure.email import EmailDeliveryError, EmailSender


class ContactServiceError(Exception):
    """Raised when a contact request cannot be processed safely."""


class ContactService:
    def __init__(self, email_sender: EmailSender) -> None:
        self._email_sender = email_sender

    def submit_contact_request(self, submission: ContactSubmission) -> None:
        try:
            self._email_sender.send_contact_request(submission)
        except EmailDeliveryError as exc:
            raise ContactServiceError("Unable to send contact request.") from exc
