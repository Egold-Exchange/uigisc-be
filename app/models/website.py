from datetime import datetime
from typing import Optional, Dict
from pydantic import BaseModel, Field
from bson import ObjectId


class WebsiteModel(BaseModel):
    """User website/site database model."""
    id: Optional[str] = Field(default=None, alias="_id")
    user_id: str  # Reference to user
    subdomain: str  # Unique subdomain (same as user.subdomain)
    opportunity_link: str = ""  # User's main referral link
    can_update_referral: bool = True
    status: str = "unpublished"  # "active" or "unpublished"
    customizations: Dict[str, str] = {}  # opportunity_id -> custom_link
    date_published: Optional[datetime] = None
    last_modified: datetime = Field(default_factory=datetime.utcnow)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: str}


def website_helper(website: dict) -> dict:
    """Convert MongoDB website document to dict."""
    return {
        "id": str(website["_id"]),
        "user_id": str(website["user_id"]),
        "subdomain": website["subdomain"],
        "opportunity_link": website.get("opportunity_link", ""),
        "can_update_referral": website.get("can_update_referral", True),
        "status": website.get("status", "unpublished"),
        "customizations": website.get("customizations", {}),
        "date_published": website.get("date_published"),
        "last_modified": website.get("last_modified"),
        "created_at": website.get("created_at"),
    }
