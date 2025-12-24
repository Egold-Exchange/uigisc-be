from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from bson import ObjectId


class PartnerItem(BaseModel):
    """Partner logo item."""
    id: str
    image_url: str
    name: str = ""
    order: int = 0


class SiteSettingsModel(BaseModel):
    """Site settings database model."""
    id: Optional[str] = Field(default=None, alias="_id")
    hero_video_url: str = ""
    partners: List[PartnerItem] = []
    last_modified: datetime = Field(default_factory=datetime.utcnow)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: str}


def site_settings_helper(settings: dict) -> dict:
    """Convert MongoDB site settings document to dict."""
    return {
        "id": str(settings["_id"]),
        "hero_video_url": settings.get("hero_video_url", ""),
        "partners": settings.get("partners", []),
        "last_modified": settings.get("last_modified"),
        "created_at": settings.get("created_at"),
    }

