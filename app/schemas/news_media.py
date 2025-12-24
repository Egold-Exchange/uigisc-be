from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class NewsMediaCreate(BaseModel):
    """Schema for creating news media item."""
    vimeo_url: str
    title: str
    read_more_text: str = ""
    read_more_url: str = ""
    thumbnail_url: str = ""
    is_featured: bool = False
    order: Optional[int] = None


class NewsMediaUpdate(BaseModel):
    """Schema for updating news media item."""
    vimeo_url: Optional[str] = None
    title: Optional[str] = None
    read_more_text: Optional[str] = None
    read_more_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    is_featured: Optional[bool] = None
    order: Optional[int] = None
    status: Optional[str] = None


class NewsMediaResponse(BaseModel):
    """Schema for news media response (admin)."""
    id: str
    vimeo_url: str
    title: str
    read_more_text: str
    read_more_url: str
    thumbnail_url: str
    is_featured: bool
    order: int
    status: str
    date_published: Optional[datetime] = None
    last_modified: Optional[datetime] = None
    created_at: Optional[datetime] = None


class NewsMediaPublicResponse(BaseModel):
    """Schema for public news media response."""
    id: str
    vimeo_url: str
    title: str
    read_more_text: str
    read_more_url: str
    thumbnail_url: str
    is_featured: bool
    order: int

