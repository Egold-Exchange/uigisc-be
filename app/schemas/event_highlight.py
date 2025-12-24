from datetime import datetime
from typing import Optional
from pydantic import BaseModel


# ==================== EVENT CATEGORY SCHEMAS ====================

class EventCategoryCreate(BaseModel):
    """Schema for creating event category."""
    name: str
    order: Optional[int] = None


class EventCategoryUpdate(BaseModel):
    """Schema for updating event category."""
    name: Optional[str] = None
    order: Optional[int] = None
    status: Optional[str] = None


class EventCategoryResponse(BaseModel):
    """Schema for event category response (admin)."""
    id: str
    name: str
    order: int
    status: str
    created_at: Optional[datetime] = None


class EventCategoryPublicResponse(BaseModel):
    """Schema for public event category response."""
    id: str
    name: str
    order: int


# ==================== EVENT HIGHLIGHT SCHEMAS ====================

class EventHighlightCreate(BaseModel):
    """Schema for creating event highlight."""
    vimeo_url: str
    title: str
    category_id: str
    thumbnail_url: str = ""
    duration: str = ""
    is_featured: bool = False
    order: Optional[int] = None


class EventHighlightUpdate(BaseModel):
    """Schema for updating event highlight."""
    vimeo_url: Optional[str] = None
    title: Optional[str] = None
    category_id: Optional[str] = None
    thumbnail_url: Optional[str] = None
    duration: Optional[str] = None
    is_featured: Optional[bool] = None
    order: Optional[int] = None
    status: Optional[str] = None


class EventHighlightResponse(BaseModel):
    """Schema for event highlight response (admin)."""
    id: str
    vimeo_url: str
    title: str
    category_id: str
    category_name: Optional[str] = None
    thumbnail_url: str
    duration: str
    is_featured: bool
    order: int
    status: str
    date_published: Optional[datetime] = None
    last_modified: Optional[datetime] = None
    created_at: Optional[datetime] = None


class EventHighlightPublicResponse(BaseModel):
    """Schema for public event highlight response."""
    id: str
    vimeo_url: str
    title: str
    category_id: str
    category_name: Optional[str] = None
    thumbnail_url: str
    duration: str
    is_featured: bool
    order: int

