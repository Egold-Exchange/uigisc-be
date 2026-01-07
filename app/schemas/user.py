from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class UserCreate(BaseModel):
    """Schema for user registration."""
    email: EmailStr
    password: str = Field(..., min_length=8)
    subdomain: str = Field(..., min_length=3, max_length=30, pattern=r"^[a-zA-Z0-9]+$")
    name: str = Field(..., min_length=2, max_length=50)
    mobile: str = Field(..., min_length=8, max_length=20)


class UserLogin(BaseModel):
    """Schema for user login."""
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """Schema for user response (public info)."""
    id: str
    email: str
    subdomain: Optional[str] = None
    name: Optional[str] = None
    mobile: Optional[str] = None
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


class SendVerificationCodeRequest(BaseModel):
    """Schema for requesting verification code via SNS/SES."""
    email: EmailStr


class VerifyCodeRequest(BaseModel):
    """Schema for verifying a code."""
    email: EmailStr
    code: str = Field(..., min_length=6, max_length=6)


class VerificationCodeResponse(BaseModel):
    """Schema for verification code response."""
    success: bool
    message: str
    dev_code: Optional[str] = None  # Only returned in development mode


class PasswordChange(BaseModel):
    """Schema for password change."""
    current_password: str
    new_password: str = Field(..., min_length=8)


class ForgotPasswordRequest(BaseModel):
    """Schema for requesting password reset code."""
    email: EmailStr


class VerifyResetCodeRequest(BaseModel):
    """Schema for verifying password reset code."""
    email: EmailStr
    code: str = Field(..., min_length=6, max_length=6)


class ResetPasswordRequest(BaseModel):
    """Schema for resetting password with verified code."""
    email: EmailStr
    code: str = Field(..., min_length=6, max_length=6)
    new_password: str = Field(..., min_length=8)
