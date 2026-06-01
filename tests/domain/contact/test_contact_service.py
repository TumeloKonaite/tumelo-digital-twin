from __future__ import annotations

from unittest.mock import Mock, call
from uuid import uuid4

import pytest

from src.app.domain.contact import ContactService, ContactServiceError
from src.app.infrastructure.email import EmailDeliveryError


def test_contact_service_submits_contact_request(contact_submission) -> None:
    tracker = Mock()
    email_sender = Mock()
    repository = Mock()
    repository.create.return_value = uuid4()
    tracker.attach_mock(repository, "repository")
    tracker.attach_mock(email_sender, "email_sender")
    service = ContactService(email_sender=email_sender, repository=repository)

    service.submit_contact_request(contact_submission)

    repository.create.assert_called_once_with(contact_submission)
    email_sender.send_contact_request.assert_called_once_with(contact_submission)
    repository.mark_email_sent.assert_called_once_with(
        repository.create.return_value
    )
    repository.mark_email_failed.assert_not_called()
    assert tracker.mock_calls == [
        call.repository.create(contact_submission),
        call.email_sender.send_contact_request(contact_submission),
        call.repository.mark_email_sent(repository.create.return_value),
    ]


def test_contact_service_marks_failed_when_email_delivery_fails(
    contact_submission,
) -> None:
    tracker = Mock()
    email_sender = Mock()
    repository = Mock()
    repository.create.return_value = uuid4()
    email_sender.send_contact_request.side_effect = EmailDeliveryError("smtp failure")
    tracker.attach_mock(repository, "repository")
    tracker.attach_mock(email_sender, "email_sender")
    service = ContactService(email_sender=email_sender, repository=repository)

    with pytest.raises(ContactServiceError, match="Unable to send contact request."):
        service.submit_contact_request(contact_submission)

    repository.create.assert_called_once_with(contact_submission)
    repository.mark_email_failed.assert_called_once_with(
        repository.create.return_value,
        "smtp failure",
    )
    repository.mark_email_sent.assert_not_called()
    assert tracker.mock_calls == [
        call.repository.create(contact_submission),
        call.email_sender.send_contact_request(contact_submission),
        call.repository.mark_email_failed(
            repository.create.return_value,
            "smtp failure",
        ),
    ]


def test_contact_service_stops_when_repository_insert_fails(
    contact_submission,
) -> None:
    email_sender = Mock()
    repository = Mock()
    repository.create.side_effect = RuntimeError("database unavailable")
    service = ContactService(email_sender=email_sender, repository=repository)

    with pytest.raises(ContactServiceError, match="Unable to send contact request."):
        service.submit_contact_request(contact_submission)

    repository.create.assert_called_once_with(contact_submission)
    email_sender.send_contact_request.assert_not_called()
    repository.mark_email_sent.assert_not_called()
    repository.mark_email_failed.assert_not_called()
