from __future__ import annotations

from unittest.mock import Mock

import pytest

from src.app.domain.contact import (
    ContactService,
    ContactServiceError,
    ContactSubmission,
)
from src.app.infrastructure.email import EmailDeliveryError


def test_contact_service_submits_contact_request() -> None:
    email_sender = Mock()
    service = ContactService(email_sender=email_sender)
    submission = ContactSubmission(
        first_name="Jane",
        last_name="Doe",
        email="jane@example.com",
        phone="+27 82 123 4567",
        subject="Interested in working together",
        message="I would like to discuss a role with you.",
    )

    service.submit_contact_request(submission)

    email_sender.send_contact_request.assert_called_once_with(submission)


def test_contact_service_raises_safe_error_when_email_delivery_fails() -> None:
    email_sender = Mock()
    service = ContactService(email_sender=email_sender)
    submission = ContactSubmission(
        first_name="Jane",
        last_name="Doe",
        email="jane@example.com",
        phone="+27 82 123 4567",
        subject="Interested in working together",
        message="I would like to discuss a role with you.",
    )
    email_sender.send_contact_request.side_effect = EmailDeliveryError("smtp failure")

    with pytest.raises(ContactServiceError, match="Unable to send contact request."):
        service.submit_contact_request(submission)
