from pydantic import BaseModel, Field
from typing import Optional, Dict
from datetime import datetime


class WebsiteCreate(BaseModel):
    """Schema for creating a website (from promo page)."""
    subdomain: str = Field(..., min_length=3, max_length=30, pattern=r"^[a-zA-Z0-9]+$")
    opportunity_link: str = ""
    can_update_referral: bool = True


class WebsiteUpdate(BaseModel):
    """Schema for admin updating a website."""
    opportunity_link: Optional[str] = None
    can_update_referral: Optional[bool] = None
    status: Optional[str] = None
    customizations: Optional[Dict[str, str]] = None


class WebsiteUserUpdate(BaseModel):
    """Schema for user updating their own website links."""
    customizations: Dict[str, str] = {}  # opportunity_id -> custom_link


class WebsiteResponse(BaseModel):
    """Schema for website response."""
    id: str
    user_id: str
    subdomain: str
    opportunity_link: str
    can_update_referral: bool
    status: str
    customizations: Dict[str, str]
    date_published: Optional[datetime]
    last_modified: Optional[datetime]
    created_at: Optional[datetime]


class WebsitePublicResponse(BaseModel):
    """Schema for public website data (for user sites)."""
    subdomain: str
    opportunity_link: str
    customizations: Dict[str, str]
