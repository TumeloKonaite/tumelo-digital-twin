from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from src.app.api.schemas.contact import ContactRequest, ContactResponse
from src.app.core.dependencies import get_contact_service
from src.app.domain.contact import (
    ContactService,
    ContactServiceError,
    ContactSubmission,
)

router = APIRouter()


@router.post(
    "/api/contact",
    response_model=ContactResponse,
    status_code=status.HTTP_200_OK,
)
def submit_contact_request(
    request: ContactRequest,
    contact_service: ContactService = Depends(get_contact_service),
) -> ContactResponse:
    try:
        contact_service.submit_contact_request(
            ContactSubmission(**request.model_dump())
        )
    except ContactServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to send contact request.",
        ) from exc

    return ContactResponse(message="Contact request submitted successfully.")
