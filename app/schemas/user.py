from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class UserCreate(BaseModel):
    """Schema for user registration."""
    email: EmailStr
    password: str = Field(..., min_length=8)
    subdomain: str = Field(..., min_length=3, max_length=30, pattern=r"^[a-zA-Z0-9]+$")


class UserLogin(BaseModel):
    """Schema for user login."""
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """Schema for user response (public info)."""
    id: str
    email: str
    subdomain: Optional[str] = None
    role: str
    is_verified: bool
    created_at: Optional[datetime] = None


class Token(BaseModel):
    """Schema for JWT token response."""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class TokenData(BaseModel):
    """Schema for token payload data."""
    user_id: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None


class VerificationRequest(BaseModel):
    """Schema for email verification."""
    token: str


class SendVerificationRequest(BaseModel):
    """Schema for requesting verification email."""
    email: EmailStr


class PasswordChange(BaseModel):
    """Schema for password change."""
    current_password: str
    new_password: str = Field(..., min_length=8)
