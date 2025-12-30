from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime


class AddSectionContentSchema(BaseModel):
    """Schema for AddSection content."""
    member_count: Optional[str] = None
    member_count_suffix: Optional[str] = None
    member_label: Optional[str] = None
    tagline: Optional[str] = None
    description: Optional[str] = None
    promo_subtitle: Optional[str] = None
    promo_title: Optional[str] = None
    promo_tagline: Optional[str] = None
    promo_disclaimer: Optional[str] = None
    promo_image: Optional[str] = None
    promo_link: Optional[str] = None


class PageContentUpdate(BaseModel):
    """Schema for updating page content."""
    content: Dict[str, Any] = Field(..., description="Content object with section-specific fields")


class PageContentResponse(BaseModel):
    """Schema for page content response."""
    id: str
    section_key: str
    content: Dict[str, Any]
    last_modified: Optional[datetime]
    created_at: Optional[datetime]


class PageContentPublicResponse(BaseModel):
    """Schema for public page content response."""
    section_key: str
    content: Dict[str, Any]

