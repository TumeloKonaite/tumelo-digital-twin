from __future__ import annotations

from pydantic import BaseModel

from src.app.domain.contact import ContactSubmissionPayload


class ContactRequest(ContactSubmissionPayload):
    pass


class ContactResponse(BaseModel):
    message: str
