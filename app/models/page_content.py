from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from bson import ObjectId


class AddSectionContent(BaseModel):
    """Content for the AddSection component."""
    # Left card - Member Stats
    member_count: str = "300,000"
    member_count_suffix: str = "+"
    member_label: str = "satisfied\nmembers"
    tagline: str = "One simple rule: grow together."
    description: str = "We live by the 1/3 Rule to Success — a balance of learning, earning, and sharing. And it works. Every story in our group is proof that the future belongs to those who show up and play the long game."
    
    # Right card - Car Promo
    promo_subtitle: str = "This is your chance to win a"
    promo_title: str = "Mercedes A Class"
    promo_tagline: str = "Only possible with UIGI-SC!"
    promo_disclaimer: str = "The model shown in pictures is only for reference. Final details will be revealed later."
    promo_image: str = ""  # URL to the car image
    promo_link: str = "/win-mercedes"


class PageContentModel(BaseModel):
    """Page content database model for storing editable section content."""
    id: Optional[str] = Field(default=None, alias="_id")
    section_key: str  # Unique identifier for the section (e.g., "add_section", "hero_section")
    content: Dict[str, Any] = {}  # Flexible content storage
    last_modified: datetime = Field(default_factory=datetime.utcnow)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: str}


def page_content_helper(content: dict) -> dict:
    """Convert MongoDB page content document to dict."""
    return {
        "id": str(content["_id"]),
        "section_key": content.get("section_key", ""),
        "content": content.get("content", {}),
        "last_modified": content.get("last_modified"),
        "created_at": content.get("created_at"),
    }


# Default content for AddSection
DEFAULT_ADD_SECTION_CONTENT = {
    "member_count": "300,000",
    "member_count_suffix": "+",
    "member_label": "satisfied\nmembers",
    "tagline": "One simple rule: grow together.",
    "description": "We live by the 1/3 Rule to Success — a balance of learning, earning, and sharing. And it works. Every story in our group is proof that the future belongs to those who show up and play the long game.",
    "promo_subtitle": "This is your chance to win a",
    "promo_title": "Mercedes A Class",
    "promo_tagline": "Only possible with UIGI-SC!",
    "promo_disclaimer": "The model shown in pictures is only for reference. Final details will be revealed later.",
    "promo_image": "",
    "promo_link": "/win-mercedes"
}

# Default content for Products Header Section
DEFAULT_PRODUCTS_HEADER_CONTENT = {
    "title": "Make Money\nWith UIGISC",
    "description": "Discover diverse ways to grow — from crypto and wellness to savings, clean energy, and more — all shared and tested by our 300,000+ member community."
}

# Map of section keys to default content
DEFAULT_CONTENT_MAP = {
    "add_section": DEFAULT_ADD_SECTION_CONTENT,
    "products_header": DEFAULT_PRODUCTS_HEADER_CONTENT,
}

