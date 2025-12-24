from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class PartnerItem(BaseModel):
    """Partner logo item schema."""
    id: str
    image_url: str
    name: str = ""
    link: str = ""
    order: int = 0


class PartnerItemCreate(BaseModel):
    """Schema for creating a partner item."""
    image_url: str
    name: str = ""
    link: str = ""


class SocialLinks(BaseModel):
    """Social media links schema."""
    facebook: str = ""
    instagram: str = ""
    twitter: str = ""
    youtube: str = ""
    tiktok: str = ""
    telegram: str = ""


class SocialLinksUpdate(BaseModel):
    """Schema for updating social links."""
    facebook: Optional[str] = None
    instagram: Optional[str] = None
    twitter: Optional[str] = None
    youtube: Optional[str] = None
    tiktok: Optional[str] = None
    telegram: Optional[str] = None


class SiteSettingsUpdate(BaseModel):
    """Schema for updating site settings."""
    hero_video_url: Optional[str] = None
    facebook_group_link: Optional[str] = None
    social_links: Optional[SocialLinksUpdate] = None


class SiteSettingsResponse(BaseModel):
    """Schema for site settings response."""
    id: str
    hero_video_url: str
    facebook_group_link: str
    partners: List[PartnerItem]
    social_links: SocialLinks
    last_modified: Optional[datetime]
    created_at: Optional[datetime]


class SiteSettingsPublicResponse(BaseModel):
    """Schema for public site settings (no admin fields)."""
    hero_video_url: str
    facebook_group_link: str
    partners: List[PartnerItem]
    social_links: SocialLinks


class PartnerReorderRequest(BaseModel):
    """Schema for reordering partners."""
    partner_ids: List[str] = Field(..., min_items=1)

