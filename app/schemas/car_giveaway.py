from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


class CarGiveawaySubmissionCreate(BaseModel):
    """Schema for public car giveaway form submission."""
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    phone: str = Field(..., min_length=7, max_length=25)
    email: EmailStr
    agreed_to_rules: bool

    @field_validator("first_name", "last_name", "phone")
    @classmethod
    def validate_non_empty_trimmed(cls, value: str) -> str:
        trimmed = value.strip()
        if not trimmed:
            raise ValueError("Field cannot be empty")
        return trimmed

    @field_validator("agreed_to_rules")
    @classmethod
    def validate_rules_agreement(cls, value: bool) -> bool:
        if not value:
            raise ValueError("You must agree to the rules and information")
        return value


class CarGiveawaySubmissionResponse(BaseModel):
    """Schema for car giveaway submission response."""
    id: str
    first_name: str
    last_name: str
    phone: str
    email: str
    agreed_to_rules: bool
    created_at: Optional[datetime] = None
