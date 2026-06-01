from __future__ import annotations

from unittest.mock import Mock, call
from uuid import uuid4

import pytest

from src.app.domain.contact import (
    ContactService,
    ContactServiceError,
    ContactSubmission,
)
from src.app.infrastructure.email import EmailDeliveryError


def test_contact_service_submits_contact_request() -> None:
    tracker = Mock()
    email_sender = Mock()
    repository = Mock()
    repository.create.return_value = uuid4()
    tracker.attach_mock(repository, "repository")
    tracker.attach_mock(email_sender, "email_sender")
    service = ContactService(email_sender=email_sender, repository=repository)
    submission = ContactSubmission(
        first_name="Jane",
        last_name="Doe",
        email="jane@example.com",
        phone="+27 82 123 4567",
        subject="Interested in working together",
        message="I would like to discuss a role with you.",
    )

    service.submit_contact_request(submission)

    repository.create.assert_called_once_with(submission)
    email_sender.send_contact_request.assert_called_once_with(submission)
    repository.mark_email_sent.assert_called_once_with(repository.create.return_value)
    repository.mark_email_failed.assert_not_called()
    assert tracker.mock_calls == [
        call.repository.create(submission),
        call.email_sender.send_contact_request(submission),
        call.repository.mark_email_sent(repository.create.return_value),
    ]


def test_contact_service_raises_safe_error_when_email_delivery_fails() -> None:
    tracker = Mock()
    email_sender = Mock()
    repository = Mock()
    repository.create.return_value = uuid4()
    tracker.attach_mock(repository, "repository")
    tracker.attach_mock(email_sender, "email_sender")
    service = ContactService(email_sender=email_sender, repository=repository)
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

    repository.create.assert_called_once_with(submission)
    repository.mark_email_failed.assert_called_once_with(
        repository.create.return_value,
        "smtp failure",
    )
    repository.mark_email_sent.assert_not_called()
    assert tracker.mock_calls == [
        call.repository.create(submission),
        call.email_sender.send_contact_request(submission),
        call.repository.mark_email_failed(
            repository.create.return_value,
            "smtp failure",
        ),
    ]


def test_contact_service_stops_when_repository_insert_fails() -> None:
    email_sender = Mock()
    repository = Mock()
    repository.create.side_effect = RuntimeError("database unavailable")
    service = ContactService(email_sender=email_sender, repository=repository)
    submission = ContactSubmission(
        first_name="Jane",
        last_name="Doe",
        email="jane@example.com",
        phone="+27 82 123 4567",
        subject="Interested in working together",
        message="I would like to discuss a role with you.",
    )

    with pytest.raises(ContactServiceError, match="Unable to send contact request."):
        service.submit_contact_request(submission)

    repository.create.assert_called_once_with(submission)
    email_sender.send_contact_request.assert_not_called()
    repository.mark_email_sent.assert_not_called()
    repository.mark_email_failed.assert_not_called()
