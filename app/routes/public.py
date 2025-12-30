from typing import List
from fastapi import APIRouter, HTTPException

from app.database import get_database
from app.schemas.opportunity import OpportunityPublicResponse
from app.schemas.website import WebsitePublicResponse
from app.schemas.site_settings import SiteSettingsPublicResponse
from app.schemas.news_media import NewsMediaPublicResponse
from app.schemas.event_highlight import EventCategoryPublicResponse, EventHighlightPublicResponse
from app.schemas.page_content import PageContentPublicResponse
from app.models.opportunity import opportunity_helper
from app.models.site_settings import site_settings_helper
from app.models.news_media import news_media_helper
from app.models.event_highlight import event_category_helper, event_highlight_helper
from app.models.page_content import DEFAULT_CONTENT_MAP

router = APIRouter()


@router.get("/opportunities", response_model=List[OpportunityPublicResponse])
async def get_public_opportunities():
    """Get all active opportunities for the homepage."""
    db = get_database()
    
    opportunities = []
    cursor = db.opportunities.find({"status": "active"}).sort("order", 1)
    
    async for opp in cursor:
        opp_id = str(opp["_id"])
        
        primary_button = opp.get("primary_button")
            
        opportunities.append(OpportunityPublicResponse(
            id=opp_id,
            name=opp["name"],
            image=opp.get("image", ""),
            description=opp.get("description", ""),
            videos=opp.get("videos", []),
            bottom_description=opp.get("bottom_description", ""),
            telegram_link=opp.get("telegram_link"),
            primary_button=primary_button,
            secondary_button=opp.get("secondary_button"),
            status=opp.get("status", "active"),
            is_featured=opp.get("is_featured", False),
            order=opp.get("order", 0)
        ))
    
    return opportunities


@router.get("/check-subdomain/{subdomain}")
async def check_subdomain_availability(subdomain: str):
    """Check if a subdomain is available."""
    db = get_database()
    
    # Validate subdomain format
    if len(subdomain) < 3 or len(subdomain) > 30:
        return {"available": False, "message": "Subdomain must be 3-30 characters"}
    
    if not subdomain.isalnum():
        return {"available": False, "message": "Subdomain can only contain letters and numbers"}
    
    # Reserved subdomains
    reserved = ["admin", "api", "www", "mail", "ftp", "app", "dashboard", "login"]
    if subdomain.lower() in reserved:
        return {"available": False, "message": "This subdomain is reserved"}
    
    # Check database
    existing = await db.users.find_one({"subdomain": subdomain.lower()})
    if existing:
        return {"available": False, "message": "Subdomain already taken"}
    
    return {"available": True, "message": "Subdomain is available"}
    
    
@router.get("/site/{subdomain}", response_model=WebsitePublicResponse)
async def get_user_site(subdomain: str):
    """Get public data for a user site."""
    db = get_database()
    
    site = await db.websites.find_one({
        "subdomain": subdomain.lower(),
        "status": "active"
    })
    
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    
    return WebsitePublicResponse(
        subdomain=site["subdomain"],
        customizations=site.get("customizations", {})
    )


@router.get("/site/{subdomain}/opportunities", response_model=List[OpportunityPublicResponse])
async def get_site_opportunities(subdomain: str):
    """Get opportunities for a specific user site with customizations applied."""
    db = get_database()
    
    # Get site
    site = await db.websites.find_one({
        "subdomain": subdomain.lower(),
        "status": "active"
    })
    
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    
    customizations = site.get("customizations", {})
    
    # Get opportunities
    opportunities = []
    cursor = db.opportunities.find({"status": "active"}).sort("order", 1)
    
    async for opp in cursor:
        opp_id = str(opp["_id"])
        
        # Apply customizations if any
        primary_button = opp.get("primary_button")
        
        if opp_id in customizations and customizations[opp_id]:
            # Override primary button link with user's custom link
            if primary_button:
                primary_button = {**primary_button, "link": customizations[opp_id]}
            else:
                # If primary_button doesn't exist but customization does
                primary_button = {"text": "Join Now", "link": customizations[opp_id]}
        
        opportunities.append(OpportunityPublicResponse(
            id=opp_id,
            name=opp["name"],
            image=opp.get("image", ""),
            description=opp.get("description", ""),
            videos=opp.get("videos", []),
            bottom_description=opp.get("bottom_description", ""),
            telegram_link=opp.get("telegram_link"),
            primary_button=primary_button,
            secondary_button=opp.get("secondary_button"),
            status=opp.get("status", "active"),
            is_featured=opp.get("is_featured", False),
            order=opp.get("order", 0)
        ))
    
    return opportunities


@router.get("/site-settings", response_model=SiteSettingsPublicResponse)
async def get_public_site_settings():
    """Get public site settings (hero video URL, partners, and social links)."""
    db = get_database()
    
    settings = await db.site_settings.find_one()
    
    default_social_links = {
        "facebook": "",
        "instagram": "",
        "twitter": "",
        "youtube": "",
        "tiktok": "",
        "telegram": ""
    }
    
    if not settings:
        # Return default empty settings
        return SiteSettingsPublicResponse(
            hero_video_url="",
            facebook_group_link="",
            partners=[],
            social_links=default_social_links
        )
    
    # Sort partners by order
    partners = sorted(settings.get("partners", []), key=lambda p: p.get("order", 0))
    
    return SiteSettingsPublicResponse(
        hero_video_url=settings.get("hero_video_url", ""),
        facebook_group_link=settings.get("facebook_group_link", ""),
        partners=partners,
        social_links=settings.get("social_links", default_social_links)
    )


@router.get("/news-media", response_model=List[NewsMediaPublicResponse])
async def get_public_news_media():
    """Get all active news and media items for the public page (newest first)."""
    db = get_database()
    
    items = []
    # Sort by created_at descending (newest first)
    cursor = db.news_media.find({"status": "active"}).sort("created_at", -1)
    
    async for item in cursor:
        items.append(NewsMediaPublicResponse(
            id=str(item["_id"]),
            vimeo_url=item.get("vimeo_url", ""),
            title=item.get("title", ""),
            read_more_text=item.get("read_more_text", ""),
            read_more_url=item.get("read_more_url", ""),
            thumbnail_url=item.get("thumbnail_url", ""),
            is_featured=item.get("is_featured", False),
            order=item.get("order", 0)
        ))
    
    return items


@router.get("/event-categories", response_model=List[EventCategoryPublicResponse])
async def get_public_event_categories():
    """Get all active event categories."""
    db = get_database()
    
    categories = []
    cursor = db.event_categories.find({"status": "active"}).sort("order", 1)
    
    async for category in cursor:
        categories.append(EventCategoryPublicResponse(
            id=str(category["_id"]),
            name=category.get("name", ""),
            order=category.get("order", 0)
        ))
    
    return categories


@router.get("/event-highlights", response_model=List[EventHighlightPublicResponse])
async def get_public_event_highlights(category_id: str = None):
    """Get all active event highlights, optionally filtered by category."""
    db = get_database()
    
    # First get all active categories to map IDs to names
    categories = {}
    async for cat in db.event_categories.find({"status": "active"}):
        categories[str(cat["_id"])] = cat.get("name", "")
    
    # Build query
    query = {"status": "active"}
    if category_id:
        query["category_id"] = category_id
    
    events = []
    # Sort by order, then by created_at descending
    cursor = db.event_highlights.find(query).sort([("order", 1), ("created_at", -1)])
    
    async for event in cursor:
        # Only include events with active categories
        cat_id = event.get("category_id", "")
        if cat_id not in categories:
            continue
            
        events.append(EventHighlightPublicResponse(
            id=str(event["_id"]),
            vimeo_url=event.get("vimeo_url", ""),
            title=event.get("title", ""),
            category_id=cat_id,
            category_name=categories.get(cat_id, ""),
            thumbnail_url=event.get("thumbnail_url", ""),
            duration=event.get("duration", ""),
            is_featured=event.get("is_featured", False),
            order=event.get("order", 0)
        ))
    
    return events


@router.get("/page-content/{section_key}", response_model=PageContentPublicResponse)
async def get_public_page_content(section_key: str):
    """Get page content for a specific section (public)."""
    db = get_database()
    
    content = await db.page_content.find_one({"section_key": section_key})
    
    if not content:
        # Return default content for known sections
        default_content = DEFAULT_CONTENT_MAP.get(section_key, {})
        
        return PageContentPublicResponse(
            section_key=section_key,
            content=default_content
        )
    
    return PageContentPublicResponse(
        section_key=content.get("section_key", section_key),
        content=content.get("content", {})
    )
