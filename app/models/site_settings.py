from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from bson import ObjectId


class PartnerItem(BaseModel):
    """Partner logo item."""
    id: str
    image_url: str
    name: str = ""
    link: str = ""
    order: int = 0


class SocialLinks(BaseModel):
    """Social media links."""
    facebook: str = ""
    instagram: str = ""
    twitter: str = ""
    youtube: str = ""
    tiktok: str = ""
    telegram: str = ""


class SiteSettingsModel(BaseModel):
    """Site settings database model."""
    id: Optional[str] = Field(default=None, alias="_id")
    hero_video_url: str = ""
    facebook_group_link: str = ""
    partners: List[PartnerItem] = []
    social_links: SocialLinks = Field(default_factory=SocialLinks)
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
        "facebook_group_link": settings.get("facebook_group_link", ""),
        "partners": settings.get("partners", []),
        "social_links": settings.get("social_links", {
            "facebook": "",
            "instagram": "",
            "twitter": "",
            "youtube": "",
            "tiktok": "",
            "telegram": ""
        }),
        "last_modified": settings.get("last_modified"),
        "created_at": settings.get("created_at"),
    }

