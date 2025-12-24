from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class VideoItem(BaseModel):
    """Video item schema."""
    title: str
    vimeo_id: str


class ButtonItem(BaseModel):
    """Button configuration schema."""
    text: str
    link: str


class OpportunityCreate(BaseModel):
    """Schema for creating an opportunity."""
    name: str = Field(..., min_length=1, max_length=100)
    image: str = ""
    description: str = ""
    videos: List[VideoItem] = []
    bottom_description: str = ""
    telegram_link: Optional[str] = None
    primary_button: Optional[ButtonItem] = None
    secondary_button: Optional[ButtonItem] = None
    is_featured: bool = False
    order: int = 0


class OpportunityUpdate(BaseModel):
    """Schema for updating an opportunity."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    image: Optional[str] = None
    description: Optional[str] = None
    videos: Optional[List[VideoItem]] = None
    bottom_description: Optional[str] = None
    telegram_link: Optional[str] = None
    primary_button: Optional[ButtonItem] = None
    secondary_button: Optional[ButtonItem] = None
    status: Optional[str] = None
    is_featured: Optional[bool] = None
    order: Optional[int] = None


class OpportunityResponse(BaseModel):
    """Schema for opportunity response."""
    id: str
    name: str
    image: str
    description: str
    videos: List[VideoItem]
    bottom_description: str
    telegram_link: Optional[str]
    primary_button: Optional[ButtonItem]
    secondary_button: Optional[ButtonItem]
    status: str
    is_featured: bool
    order: int
    date_published: Optional[datetime]
    last_modified: Optional[datetime]
    created_at: Optional[datetime]


class OpportunityPublicResponse(BaseModel):
    """Schema for public opportunity response (for homepage)."""
    id: str
    name: str
    image: str
    description: str
    videos: List[VideoItem]
    bottom_description: str
    telegram_link: Optional[str]
    primary_button: Optional[ButtonItem]
    secondary_button: Optional[ButtonItem]
    status: str
    is_featured: bool
    order: int
