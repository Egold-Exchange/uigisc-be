from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime

# Reuse social link keys; optional strings for owner overrides
SOCIAL_LINK_KEYS = ("facebook", "instagram", "twitter", "youtube", "tiktok", "telegram")


class WebsiteCreate(BaseModel):
    """Schema for creating a website (from promo page)."""
    subdomain: str = Field(..., min_length=3, max_length=30, pattern=r"^[a-zA-Z0-9]+$")
    can_update_referral: bool = True


class WebsiteUpdate(BaseModel):
    """Schema for admin updating a website."""
    can_update_referral: Optional[bool] = None
    status: Optional[str] = None
    customizations: Optional[Dict[str, str]] = None


class WebsiteUserUpdate(BaseModel):
    """Schema for user updating their own website links."""
    customizations: Dict[str, str] = {}  # opportunity_id -> custom_link


class WebsiteSocialLinksUpdate(BaseModel):
    """Schema for user updating their own social links (partial; empty string = use admin default)."""
    facebook: Optional[str] = None
    instagram: Optional[str] = None
    twitter: Optional[str] = None
    youtube: Optional[str] = None
    tiktok: Optional[str] = None
    telegram: Optional[str] = None


class WebsiteResponse(BaseModel):
    """Schema for website response."""
    id: str
    user_id: str
    subdomain: str
    can_update_referral: bool
    status: str
    customizations: Dict[str, str]
    social_links: Optional[Dict[str, str]] = None
    date_published: Optional[datetime]
    last_modified: Optional[datetime]
    created_at: Optional[datetime]
    # User details (populated from user lookup)
    user_name: Optional[str] = None
    user_email: Optional[str] = None
    user_mobile: Optional[str] = None


class WebsitePublicResponse(BaseModel):
    """Schema for public website data (for user sites)."""
    subdomain: str
    customizations: Dict[str, str]
    social_links: Optional[Dict[str, str]] = None
