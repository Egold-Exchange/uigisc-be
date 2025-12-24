from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from bson import ObjectId


class NewsMediaModel(BaseModel):
    """News and Media database model."""
    id: Optional[str] = Field(default=None, alias="_id")
    vimeo_url: str = ""
    title: str = ""
    read_more_text: str = ""
    read_more_url: str = ""
    thumbnail_url: str = ""
    is_featured: bool = False
    order: int = 0
    status: str = "unpublished"
    date_published: Optional[datetime] = None
    last_modified: datetime = Field(default_factory=datetime.utcnow)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: str}


def news_media_helper(news: dict) -> dict:
    """Convert MongoDB news media document to dict."""
    return {
        "id": str(news["_id"]),
        "vimeo_url": news.get("vimeo_url", ""),
        "title": news.get("title", ""),
        "read_more_text": news.get("read_more_text", ""),
        "read_more_url": news.get("read_more_url", ""),
        "thumbnail_url": news.get("thumbnail_url", ""),
        "is_featured": news.get("is_featured", False),
        "order": news.get("order", 0),
        "status": news.get("status", "unpublished"),
        "date_published": news.get("date_published"),
        "last_modified": news.get("last_modified"),
        "created_at": news.get("created_at"),
    }

