from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from bson import ObjectId


class EventCategoryModel(BaseModel):
    """Event Category database model."""
    id: Optional[str] = Field(default=None, alias="_id")
    name: str = ""
    order: int = 0
    status: str = "active"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: str}


class EventHighlightModel(BaseModel):
    """Event Highlight database model."""
    id: Optional[str] = Field(default=None, alias="_id")
    vimeo_url: str = ""
    title: str = ""
    category_id: str = ""
    thumbnail_url: str = ""
    duration: str = ""  # e.g., "37:23", "1:31"
    is_featured: bool = False
    order: int = 0
    status: str = "unpublished"
    date_published: Optional[datetime] = None
    last_modified: datetime = Field(default_factory=datetime.utcnow)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: str}


def event_category_helper(category: dict) -> dict:
    """Convert MongoDB event category document to dict."""
    return {
        "id": str(category["_id"]),
        "name": category.get("name", ""),
        "order": category.get("order", 0),
        "status": category.get("status", "active"),
        "created_at": category.get("created_at"),
    }


def event_highlight_helper(event: dict) -> dict:
    """Convert MongoDB event highlight document to dict."""
    return {
        "id": str(event["_id"]),
        "vimeo_url": event.get("vimeo_url", ""),
        "title": event.get("title", ""),
        "category_id": event.get("category_id", ""),
        "thumbnail_url": event.get("thumbnail_url", ""),
        "duration": event.get("duration", ""),
        "is_featured": event.get("is_featured", False),
        "order": event.get("order", 0),
        "status": event.get("status", "unpublished"),
        "date_published": event.get("date_published"),
        "last_modified": event.get("last_modified"),
        "created_at": event.get("created_at"),
    }

