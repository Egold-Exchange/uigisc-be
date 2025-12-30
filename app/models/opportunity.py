from datetime import datetime
from typing import Optional, List, Literal
from pydantic import BaseModel, Field
from bson import ObjectId


class VideoItem(BaseModel):
    """Video item for opportunity."""
    title: str
    vimeo_id: str


class ButtonItem(BaseModel):
    """Button configuration."""
    text: str
    link: str
    type: Literal['link', 'copy'] = 'link'


class OpportunityModel(BaseModel):
    """Opportunity/Product database model."""
    id: Optional[str] = Field(default=None, alias="_id")
    name: str
    image: str = ""  # URL or base64
    description: str = ""
    videos: List[VideoItem] = []
    bottom_description: str = ""  # Description shown after videos
    telegram_link: Optional[str] = None
    primary_button: Optional[ButtonItem] = None
    secondary_button: Optional[ButtonItem] = None
    status: str = "unpublished"  # "active" or "unpublished"
    is_featured: bool = False
    order: int = 0
    date_published: Optional[datetime] = None
    last_modified: datetime = Field(default_factory=datetime.utcnow)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: str}


def opportunity_helper(opportunity: dict) -> dict:
    """Convert MongoDB opportunity document to dict."""
    return {
        "id": str(opportunity["_id"]),
        "name": opportunity["name"],
        "image": opportunity.get("image", ""),
        "description": opportunity.get("description", ""),
        "videos": opportunity.get("videos", []),
        "bottom_description": opportunity.get("bottom_description", ""),
        "telegram_link": opportunity.get("telegram_link"),
        "primary_button": opportunity.get("primary_button"),
        "secondary_button": opportunity.get("secondary_button"),
        "status": opportunity.get("status", "unpublished"),
        "is_featured": opportunity.get("is_featured", False),
        "order": opportunity.get("order", 0),
        "date_published": opportunity.get("date_published"),
        "last_modified": opportunity.get("last_modified"),
        "created_at": opportunity.get("created_at"),
    }
