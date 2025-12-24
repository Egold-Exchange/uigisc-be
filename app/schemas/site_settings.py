from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class PartnerItem(BaseModel):
    """Partner logo item schema."""
    id: str
    image_url: str
    name: str = ""
    order: int = 0


class PartnerItemCreate(BaseModel):
    """Schema for creating a partner item."""
    image_url: str
    name: str = ""


class SiteSettingsUpdate(BaseModel):
    """Schema for updating site settings."""
    hero_video_url: Optional[str] = None


class SiteSettingsResponse(BaseModel):
    """Schema for site settings response."""
    id: str
    hero_video_url: str
    partners: List[PartnerItem]
    last_modified: Optional[datetime]
    created_at: Optional[datetime]


class SiteSettingsPublicResponse(BaseModel):
    """Schema for public site settings (no admin fields)."""
    hero_video_url: str
    partners: List[PartnerItem]


class PartnerReorderRequest(BaseModel):
    """Schema for reordering partners."""
    partner_ids: List[str] = Field(..., min_items=1)

