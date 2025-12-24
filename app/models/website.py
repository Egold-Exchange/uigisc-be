from datetime import datetime
from typing import Optional, Dict
from pydantic import BaseModel, Field
from bson import ObjectId


class WebsiteModel(BaseModel):
    """User website/site database model."""
    id: Optional[str] = Field(default=None, alias="_id")
    user_id: str  # Reference to user
    subdomain: str  # Unique subdomain (same as user.subdomain)
    can_update_referral: bool = True
    status: str = "unpublished"  # "active" or "unpublished"
    customizations: Dict[str, str] = {}  # opportunity_id -> custom_link
    date_published: Optional[datetime] = None
    last_modified: datetime = Field(default_factory=datetime.utcnow)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: str}


def website_helper(website: dict, user: dict = None) -> dict:
    """Convert MongoDB website document to dict.
    
    Args:
        website: The website document from MongoDB
        user: Optional user document to include user details
    """
    result = {
        "id": str(website["_id"]),
        "user_id": str(website["user_id"]),
        "subdomain": website["subdomain"],
        "can_update_referral": website.get("can_update_referral", True),
        "status": website.get("status", "unpublished"),
        "customizations": website.get("customizations", {}),
        "date_published": website.get("date_published"),
        "last_modified": website.get("last_modified"),
        "created_at": website.get("created_at"),
    }
    
    # Add user details if provided
    if user:
        result["user_name"] = user.get("name")
        result["user_email"] = user.get("email")
        result["user_mobile"] = user.get("mobile")
    else:
        result["user_name"] = None
        result["user_email"] = None
        result["user_mobile"] = None
    
    return result
