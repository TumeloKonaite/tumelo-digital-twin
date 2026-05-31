from __future__ import annotations

from email.message import EmailMessage
from unittest.mock import MagicMock, patch

import pytest

from src.app.domain.contact import ContactSubmission
from src.app.infrastructure.email import EmailDeliveryError
from src.app.infrastructure.email.smtp_email_sender import SMTPEmailSender


def test_smtp_email_sender_sends_contact_request() -> None:
    sender = SMTPEmailSender(
        host="smtp.example.com",
        port=587,
        username="mailer",
        password="secret",
        from_email="portfolio@example.com",
        to_email="owner@example.com",
        use_tls=True,
    )
    submission = ContactSubmission(
        first_name="Jane",
        last_name="Doe",
        email="jane@example.com",
        phone="+27 82 123 4567",
        subject="Interested in working together",
        message="I would like to discuss a role with you.",
    )

    with patch("src.app.infrastructure.email.smtp_email_sender.smtplib.SMTP") as smtp:
        client = MagicMock()
        smtp.return_value.__enter__.return_value = client

        sender.send_contact_request(submission)

    client.ehlo.assert_called()
    client.starttls.assert_called_once_with()
    client.login.assert_called_once_with("mailer", "secret")
    client.send_message.assert_called_once()

    sent_message = client.send_message.call_args.args[0]
    assert isinstance(sent_message, EmailMessage)
    assert (
        sent_message["Subject"]
        == "Portfolio contact request: Interested in working together"
    )
    assert sent_message["From"] == "portfolio@example.com"
    assert sent_message["To"] == "owner@example.com"
    assert sent_message["Reply-To"] == "jane@example.com"
    assert "First name: Jane" in sent_message.get_content()
    assert "I would like to discuss a role with you." in sent_message.get_content()


def test_smtp_email_sender_raises_when_configuration_is_invalid() -> None:
    sender = SMTPEmailSender(
        host=None,
        port=587,
        username=None,
        password=None,
        from_email="portfolio@example.com",
        to_email="owner@example.com",
        use_tls=True,
    )

    with pytest.raises(EmailDeliveryError, match="Unable to send contact request."):
        sender.send_contact_request(
            ContactSubmission(
                first_name="Jane",
                last_name="Doe",
                email="jane@example.com",
                phone="+27 82 123 4567",
                subject="Interested in working together",
                message="I would like to discuss a role with you.",
            )
        )
