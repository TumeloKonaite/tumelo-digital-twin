from __future__ import annotations

from unittest.mock import Mock

import pytest

from src.app.core.dependencies import get_contact_service
from src.app.domain.contact import ContactServiceError, ContactSubmission


@pytest.fixture
def contact_service_override(app):
    service = Mock()
    app.dependency_overrides[get_contact_service] = lambda: service
    yield service
    app.dependency_overrides.clear()


def test_contact_route_returns_success(client, contact_service_override) -> None:
    payload = {
        "first_name": "Jane",
        "last_name": "Doe",
        "email": "Jane@Example.com",
        "phone": "+27 82 123 4567",
        "subject": "Interested in working together",
        "message": "I would like to discuss a role with you.",
    }

    response = client.post("/api/contact", json=payload)

    assert response.status_code == 200
    assert response.json() == {"message": "Contact request submitted successfully."}
    contact_service_override.submit_contact_request.assert_called_once_with(
        ContactSubmission(
            first_name="Jane",
            last_name="Doe",
            email="jane@example.com",
            phone="+27 82 123 4567",
            subject="Interested in working together",
            message="I would like to discuss a role with you.",
        )
    )


def test_contact_route_returns_500_when_sender_fails(
    client, contact_service_override
) -> None:
    contact_service_override.submit_contact_request.side_effect = ContactServiceError(
        "smtp failure"
    )

    response = client.post(
        "/api/contact",
        json={
            "first_name": "Jane",
            "last_name": "Doe",
            "email": "jane@example.com",
            "phone": "+27 82 123 4567",
            "subject": "Interested in working together",
            "message": "I would like to discuss a role with you.",
        },
    )

    assert response.status_code == 500
    assert response.json() == {"detail": "Unable to send contact request."}


def test_contact_route_rejects_invalid_payload(
    client, contact_service_override
) -> None:
    response = client.post(
        "/api/contact",
        json={
            "first_name": "Jane",
            "last_name": "Doe",
            "email": "not-an-email",
            "phone": "+27 82 123 4567",
            "subject": "Hi",
            "message": "short",
        },
    )

    assert response.status_code == 422
    contact_service_override.submit_contact_request.assert_not_called()


def test_contact_route_resolves_contact_service_from_app_state(client, app) -> None:
    payload = {
        "first_name": "Jane",
        "last_name": "Doe",
        "email": "jane@example.com",
        "phone": "+27 82 123 4567",
        "subject": "Interested in working together",
        "message": "I would like to discuss a role with you.",
    }
    submit_contact_request = Mock()
    app.state.dependencies.contact_service.submit_contact_request = (
        submit_contact_request
    )

    response = client.post("/api/contact", json=payload)

    assert response.status_code == 200
    assert response.json() == {"message": "Contact request submitted successfully."}
    submit_contact_request.assert_called_once_with(
        ContactSubmission(
            first_name="Jane",
            last_name="Doe",
            email="jane@example.com",
            phone="+27 82 123 4567",
            subject="Interested in working together",
            message="I would like to discuss a role with you.",
        )
    )


def test_contact_route_requires_all_required_fields(
    client, contact_service_override
) -> None:
    response = client.post(
        "/api/contact",
        json={
            "first_name": "Jane",
            "last_name": "Doe",
            "phone": "+27 82 123 4567",
            "subject": "Interested in working together",
            "message": "I would like to discuss a role with you.",
        },
    )

    assert response.status_code == 422
    contact_service_override.submit_contact_request.assert_not_called()
