from __future__ import annotations

from dataclasses import fields

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .models import ContactSubmission

EMAIL_PATTERN = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"


class ContactSubmissionPayload(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    email: str = Field(..., min_length=3, max_length=320, pattern=EMAIL_PATTERN)
    phone: str = Field(..., min_length=7, max_length=32)
    subject: str = Field(..., min_length=3, max_length=200)
    message: str = Field(..., min_length=10, max_length=5000)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.lower()

    def to_submission(self) -> ContactSubmission:
        submission_field_names = {field.name for field in fields(ContactSubmission)}
        payload = self.model_dump(include=submission_field_names)
        return ContactSubmission(**payload)
