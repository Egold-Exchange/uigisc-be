from datetime import datetime
from typing import List
from fastapi import APIRouter, HTTPException, status, Depends, File, UploadFile
from bson import ObjectId

from app.database import get_database
from app.schemas.opportunity import (
    OpportunityCreate, OpportunityUpdate, OpportunityResponse
)
from app.schemas.website import WebsiteUpdate, WebsiteResponse
from app.schemas.site_settings import (
    SiteSettingsUpdate, SiteSettingsResponse, PartnerItemCreate,
    PartnerReorderRequest, PartnerItem
)
from app.schemas.news_media import (
    NewsMediaCreate, NewsMediaUpdate, NewsMediaResponse
)
from app.schemas.event_highlight import (
    EventCategoryCreate, EventCategoryUpdate, EventCategoryResponse,
    EventHighlightCreate, EventHighlightUpdate, EventHighlightResponse
)
from app.middleware.auth import get_admin_user
from app.schemas.user import TokenData
from app.models.opportunity import opportunity_helper
from app.models.website import website_helper
from app.models.site_settings import site_settings_helper
from app.models.news_media import news_media_helper
from app.models.event_highlight import event_category_helper, event_highlight_helper
from app.services.storage import storage_service
import uuid

router = APIRouter()


# ==================== UTILS/STORAGE ====================

@router.post("/upload")
async def upload_image(
    file: UploadFile = File(...),
    current_user: TokenData = Depends(get_admin_user)
):
    """Upload an image to DigitalOcean Spaces (admin only)."""
    if not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an image"
        )
    
    try:
        content = await file.read()
        url = await storage_service.upload_file(
            content, 
            file.filename, 
            file.content_type
        )
        return {"url": url}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# ==================== OPPORTUNITIES ====================

@router.get("/opportunities", response_model=List[OpportunityResponse])
async def list_opportunities(current_user: TokenData = Depends(get_admin_user)):
    """List all opportunities (admin only)."""
    db = get_database()
    
    opportunities = []
    cursor = db.opportunities.find().sort("order", 1)
    
    async for opp in cursor:
        opportunities.append(OpportunityResponse(**opportunity_helper(opp)))
    
    return opportunities


@router.post("/opportunities", response_model=OpportunityResponse)
async def create_opportunity(
    opportunity: OpportunityCreate,
    current_user: TokenData = Depends(get_admin_user)
):
    """Create a new opportunity (admin only)."""
    db = get_database()
    
    # Get max order
    max_order_doc = await db.opportunities.find_one(
        sort=[("order", -1)]
    )
    next_order = (max_order_doc["order"] + 1) if max_order_doc else 0
    
    opp_doc = {
        **opportunity.model_dump(),
        "order": opportunity.order or next_order,
        "status": "unpublished",
        "date_published": None,
        "last_modified": datetime.utcnow(),
        "created_at": datetime.utcnow(),
    }
    
    result = await db.opportunities.insert_one(opp_doc)
    opp_doc["_id"] = result.inserted_id
    
    return OpportunityResponse(**opportunity_helper(opp_doc))


@router.get("/opportunities/{opportunity_id}", response_model=OpportunityResponse)
async def get_opportunity(
    opportunity_id: str,
    current_user: TokenData = Depends(get_admin_user)
):
    """Get a specific opportunity (admin only)."""
    db = get_database()
    
    try:
        opp = await db.opportunities.find_one({"_id": ObjectId(opportunity_id)})
    except:
        raise HTTPException(status_code=400, detail="Invalid opportunity ID")
    
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    
    return OpportunityResponse(**opportunity_helper(opp))


@router.put("/opportunities/{opportunity_id}", response_model=OpportunityResponse)
async def update_opportunity(
    opportunity_id: str,
    update_data: OpportunityUpdate,
    current_user: TokenData = Depends(get_admin_user)
):
    """Update an opportunity (admin only)."""
    db = get_database()
    
    try:
        opp = await db.opportunities.find_one({"_id": ObjectId(opportunity_id)})
    except:
        raise HTTPException(status_code=400, detail="Invalid opportunity ID")
    
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    
    # Build update dict
    update_dict = {k: v for k, v in update_data.model_dump().items() if v is not None}
    update_dict["last_modified"] = datetime.utcnow()
    
    # If publishing, set date_published
    if update_data.status == "active" and opp.get("status") != "active":
        update_dict["date_published"] = datetime.utcnow()
    
    await db.opportunities.update_one(
        {"_id": ObjectId(opportunity_id)},
        {"$set": update_dict}
    )
    
    updated_opp = await db.opportunities.find_one({"_id": ObjectId(opportunity_id)})
    return OpportunityResponse(**opportunity_helper(updated_opp))


@router.delete("/opportunities/{opportunity_id}")
async def delete_opportunity(
    opportunity_id: str,
    current_user: TokenData = Depends(get_admin_user)
):
    """Delete an opportunity (admin only)."""
    db = get_database()
    
    try:
        result = await db.opportunities.delete_one({"_id": ObjectId(opportunity_id)})
    except:
        raise HTTPException(status_code=400, detail="Invalid opportunity ID")
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    
    return {"message": "Opportunity deleted"}


# ==================== WEBSITES ====================

@router.get("/websites", response_model=List[WebsiteResponse])
async def list_websites(current_user: TokenData = Depends(get_admin_user)):
    """List all user websites (admin only)."""
    db = get_database()
    
    websites = []
    cursor = db.websites.find().sort("created_at", -1)
    
    async for site in cursor:
        websites.append(WebsiteResponse(**website_helper(site)))
    
    return websites


@router.get("/websites/{website_id}", response_model=WebsiteResponse)
async def get_website(
    website_id: str,
    current_user: TokenData = Depends(get_admin_user)
):
    """Get a specific website (admin only)."""
    db = get_database()
    
    try:
        site = await db.websites.find_one({"_id": ObjectId(website_id)})
    except:
        raise HTTPException(status_code=400, detail="Invalid website ID")
    
    if not site:
        raise HTTPException(status_code=404, detail="Website not found")
    
    return WebsiteResponse(**website_helper(site))


@router.put("/websites/{website_id}", response_model=WebsiteResponse)
async def update_website(
    website_id: str,
    update_data: WebsiteUpdate,
    current_user: TokenData = Depends(get_admin_user)
):
    """Update a website (admin only)."""
    db = get_database()
    
    try:
        site = await db.websites.find_one({"_id": ObjectId(website_id)})
    except:
        raise HTTPException(status_code=400, detail="Invalid website ID")
    
    if not site:
        raise HTTPException(status_code=404, detail="Website not found")
    
    update_dict = {k: v for k, v in update_data.model_dump().items() if v is not None}
    update_dict["last_modified"] = datetime.utcnow()
    
    # If publishing, set date_published
    if update_data.status == "active" and site.get("status") != "active":
        update_dict["date_published"] = datetime.utcnow()
    
    await db.websites.update_one(
        {"_id": ObjectId(website_id)},
        {"$set": update_dict}
    )
    
    updated_site = await db.websites.find_one({"_id": ObjectId(website_id)})
    return WebsiteResponse(**website_helper(updated_site))


@router.delete("/websites/{website_id}")
async def delete_website(
    website_id: str,
    current_user: TokenData = Depends(get_admin_user)
):
    """Delete a website (admin only)."""
    db = get_database()
    
    try:
        result = await db.websites.delete_one({"_id": ObjectId(website_id)})
    except:
        raise HTTPException(status_code=400, detail="Invalid website ID")
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Website not found")
    
    return {"message": "Website deleted"}


# ==================== SITE SETTINGS ====================

@router.get("/site-settings", response_model=SiteSettingsResponse)
async def get_site_settings(current_user: TokenData = Depends(get_admin_user)):
    """Get current site settings (admin only)."""
    db = get_database()
    
    settings = await db.site_settings.find_one()
    
    if not settings:
        # Initialize default settings if none exist
        default_settings = {
            "hero_video_url": "",
            "partners": [],
            "last_modified": datetime.utcnow(),
            "created_at": datetime.utcnow(),
        }
        result = await db.site_settings.insert_one(default_settings)
        default_settings["_id"] = result.inserted_id
        return SiteSettingsResponse(**site_settings_helper(default_settings))
    
    return SiteSettingsResponse(**site_settings_helper(settings))


@router.put("/site-settings", response_model=SiteSettingsResponse)
async def update_site_settings(
    update_data: SiteSettingsUpdate,
    current_user: TokenData = Depends(get_admin_user)
):
    """Update site settings (admin only)."""
    db = get_database()
    
    # Get or create settings
    settings = await db.site_settings.find_one()
    
    update_dict = {k: v for k, v in update_data.model_dump().items() if v is not None}
    update_dict["last_modified"] = datetime.utcnow()
    
    if settings:
        await db.site_settings.update_one(
            {"_id": settings["_id"]},
            {"$set": update_dict}
        )
        updated_settings = await db.site_settings.find_one({"_id": settings["_id"]})
    else:
        # Create new settings if none exist
        new_settings = {
            "hero_video_url": update_dict.get("hero_video_url", ""),
            "partners": [],
            "last_modified": datetime.utcnow(),
            "created_at": datetime.utcnow(),
        }
        result = await db.site_settings.insert_one(new_settings)
        new_settings["_id"] = result.inserted_id
        updated_settings = new_settings
    
    return SiteSettingsResponse(**site_settings_helper(updated_settings))


@router.post("/site-settings/partners", response_model=SiteSettingsResponse)
async def add_partner(
    partner_data: PartnerItemCreate,
    current_user: TokenData = Depends(get_admin_user)
):
    """Add a partner image (admin only)."""
    db = get_database()
    
    settings = await db.site_settings.find_one()
    
    # Create new partner item
    new_partner = {
        "id": str(uuid.uuid4()),
        "image_url": partner_data.image_url,
        "name": partner_data.name,
        "order": 0
    }
    
    if settings:
        # Get max order
        partners = settings.get("partners", [])
        max_order = max([p.get("order", 0) for p in partners], default=-1)
        new_partner["order"] = max_order + 1
        
        await db.site_settings.update_one(
            {"_id": settings["_id"]},
            {"$push": {"partners": new_partner}, "$set": {"last_modified": datetime.utcnow()}}
        )
        updated_settings = await db.site_settings.find_one({"_id": settings["_id"]})
    else:
        # Create new settings if none exist
        new_settings = {
            "hero_video_url": "",
            "partners": [new_partner],
            "last_modified": datetime.utcnow(),
            "created_at": datetime.utcnow(),
        }
        result = await db.site_settings.insert_one(new_settings)
        new_settings["_id"] = result.inserted_id
        updated_settings = new_settings
    
    return SiteSettingsResponse(**site_settings_helper(updated_settings))


@router.delete("/site-settings/partners/{partner_id}", response_model=SiteSettingsResponse)
async def delete_partner(
    partner_id: str,
    current_user: TokenData = Depends(get_admin_user)
):
    """Delete a partner (admin only)."""
    db = get_database()
    
    settings = await db.site_settings.find_one()
    
    if not settings:
        raise HTTPException(status_code=404, detail="Site settings not found")
    
    partners = settings.get("partners", [])
    updated_partners = [p for p in partners if p.get("id") != partner_id]
    
    if len(updated_partners) == len(partners):
        raise HTTPException(status_code=404, detail="Partner not found")
    
    await db.site_settings.update_one(
        {"_id": settings["_id"]},
        {"$set": {"partners": updated_partners, "last_modified": datetime.utcnow()}}
    )
    
    updated_settings = await db.site_settings.find_one({"_id": settings["_id"]})
    return SiteSettingsResponse(**site_settings_helper(updated_settings))


@router.put("/site-settings/partners/reorder", response_model=SiteSettingsResponse)
async def reorder_partners(
    reorder_data: PartnerReorderRequest,
    current_user: TokenData = Depends(get_admin_user)
):
    """Reorder partners (admin only)."""
    db = get_database()
    
    settings = await db.site_settings.find_one()
    
    if not settings:
        raise HTTPException(status_code=404, detail="Site settings not found")
    
    partners = settings.get("partners", [])
    partner_dict = {p.get("id"): p for p in partners}
    
    # Reorder partners based on provided order
    reordered_partners = []
    for idx, partner_id in enumerate(reorder_data.partner_ids):
        if partner_id in partner_dict:
            partner = partner_dict[partner_id]
            partner["order"] = idx
            reordered_partners.append(partner)
    
    # Add any partners not in the reorder list at the end
    for partner in partners:
        if partner.get("id") not in reorder_data.partner_ids:
            partner["order"] = len(reordered_partners)
            reordered_partners.append(partner)
    
    await db.site_settings.update_one(
        {"_id": settings["_id"]},
        {"$set": {"partners": reordered_partners, "last_modified": datetime.utcnow()}}
    )
    
    updated_settings = await db.site_settings.find_one({"_id": settings["_id"]})
    return SiteSettingsResponse(**site_settings_helper(updated_settings))


# ==================== NEWS & MEDIA ====================

@router.get("/news-media", response_model=List[NewsMediaResponse])
async def list_news_media(current_user: TokenData = Depends(get_admin_user)):
    """List all news and media items (admin only)."""
    db = get_database()
    
    items = []
    cursor = db.news_media.find().sort("order", 1)
    
    async for item in cursor:
        items.append(NewsMediaResponse(**news_media_helper(item)))
    
    return items


@router.post("/news-media", response_model=NewsMediaResponse)
async def create_news_media(
    news_data: NewsMediaCreate,
    current_user: TokenData = Depends(get_admin_user)
):
    """Create a new news/media item (admin only)."""
    db = get_database()
    
    # Get max order
    max_order_doc = await db.news_media.find_one(sort=[("order", -1)])
    next_order = (max_order_doc["order"] + 1) if max_order_doc else 0
    
    news_doc = {
        **news_data.model_dump(),
        "order": news_data.order if news_data.order is not None else next_order,
        "status": "unpublished",
        "date_published": None,
        "last_modified": datetime.utcnow(),
        "created_at": datetime.utcnow(),
    }
    
    result = await db.news_media.insert_one(news_doc)
    news_doc["_id"] = result.inserted_id
    
    return NewsMediaResponse(**news_media_helper(news_doc))


@router.get("/news-media/{item_id}", response_model=NewsMediaResponse)
async def get_news_media(
    item_id: str,
    current_user: TokenData = Depends(get_admin_user)
):
    """Get a specific news/media item (admin only)."""
    db = get_database()
    
    try:
        item = await db.news_media.find_one({"_id": ObjectId(item_id)})
    except:
        raise HTTPException(status_code=400, detail="Invalid item ID")
    
    if not item:
        raise HTTPException(status_code=404, detail="News/media item not found")
    
    return NewsMediaResponse(**news_media_helper(item))


@router.put("/news-media/{item_id}", response_model=NewsMediaResponse)
async def update_news_media(
    item_id: str,
    update_data: NewsMediaUpdate,
    current_user: TokenData = Depends(get_admin_user)
):
    """Update a news/media item (admin only)."""
    db = get_database()
    
    try:
        item = await db.news_media.find_one({"_id": ObjectId(item_id)})
    except:
        raise HTTPException(status_code=400, detail="Invalid item ID")
    
    if not item:
        raise HTTPException(status_code=404, detail="News/media item not found")
    
    # Build update dict
    update_dict = {k: v for k, v in update_data.model_dump().items() if v is not None}
    update_dict["last_modified"] = datetime.utcnow()
    
    # If publishing, set date_published
    if update_data.status == "active" and item.get("status") != "active":
        update_dict["date_published"] = datetime.utcnow()
    
    await db.news_media.update_one(
        {"_id": ObjectId(item_id)},
        {"$set": update_dict}
    )
    
    updated_item = await db.news_media.find_one({"_id": ObjectId(item_id)})
    return NewsMediaResponse(**news_media_helper(updated_item))


@router.delete("/news-media/{item_id}")
async def delete_news_media(
    item_id: str,
    current_user: TokenData = Depends(get_admin_user)
):
    """Delete a news/media item (admin only)."""
    db = get_database()
    
    try:
        result = await db.news_media.delete_one({"_id": ObjectId(item_id)})
    except:
        raise HTTPException(status_code=400, detail="Invalid item ID")
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="News/media item not found")
    
    return {"message": "News/media item deleted"}


# ==================== EVENT CATEGORIES ====================

@router.get("/event-categories", response_model=List[EventCategoryResponse])
async def list_event_categories(current_user: TokenData = Depends(get_admin_user)):
    """List all event categories (admin only)."""
    db = get_database()
    
    categories = []
    cursor = db.event_categories.find().sort("order", 1)
    
    async for category in cursor:
        categories.append(EventCategoryResponse(**event_category_helper(category)))
    
    return categories


@router.post("/event-categories", response_model=EventCategoryResponse)
async def create_event_category(
    category: EventCategoryCreate,
    current_user: TokenData = Depends(get_admin_user)
):
    """Create a new event category (admin only)."""
    db = get_database()
    
    # Get max order
    max_order_doc = await db.event_categories.find_one(sort=[("order", -1)])
    next_order = (max_order_doc["order"] + 1) if max_order_doc else 0
    
    category_doc = {
        "name": category.name,
        "order": category.order if category.order is not None else next_order,
        "status": "active",
        "created_at": datetime.utcnow(),
    }
    
    result = await db.event_categories.insert_one(category_doc)
    category_doc["_id"] = result.inserted_id
    
    return EventCategoryResponse(**event_category_helper(category_doc))


@router.get("/event-categories/{category_id}", response_model=EventCategoryResponse)
async def get_event_category(
    category_id: str,
    current_user: TokenData = Depends(get_admin_user)
):
    """Get a specific event category (admin only)."""
    db = get_database()
    
    try:
        category = await db.event_categories.find_one({"_id": ObjectId(category_id)})
    except:
        raise HTTPException(status_code=400, detail="Invalid category ID")
    
    if not category:
        raise HTTPException(status_code=404, detail="Event category not found")
    
    return EventCategoryResponse(**event_category_helper(category))


@router.put("/event-categories/{category_id}", response_model=EventCategoryResponse)
async def update_event_category(
    category_id: str,
    update_data: EventCategoryUpdate,
    current_user: TokenData = Depends(get_admin_user)
):
    """Update an event category (admin only)."""
    db = get_database()
    
    try:
        category = await db.event_categories.find_one({"_id": ObjectId(category_id)})
    except:
        raise HTTPException(status_code=400, detail="Invalid category ID")
    
    if not category:
        raise HTTPException(status_code=404, detail="Event category not found")
    
    update_dict = {k: v for k, v in update_data.model_dump().items() if v is not None}
    
    await db.event_categories.update_one(
        {"_id": ObjectId(category_id)},
        {"$set": update_dict}
    )
    
    updated_category = await db.event_categories.find_one({"_id": ObjectId(category_id)})
    return EventCategoryResponse(**event_category_helper(updated_category))


@router.delete("/event-categories/{category_id}")
async def delete_event_category(
    category_id: str,
    current_user: TokenData = Depends(get_admin_user)
):
    """Delete an event category (admin only)."""
    db = get_database()
    
    try:
        result = await db.event_categories.delete_one({"_id": ObjectId(category_id)})
    except:
        raise HTTPException(status_code=400, detail="Invalid category ID")
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Event category not found")
    
    return {"message": "Event category deleted"}


# ==================== EVENT HIGHLIGHTS ====================

@router.get("/event-highlights", response_model=List[EventHighlightResponse])
async def list_event_highlights(current_user: TokenData = Depends(get_admin_user)):
    """List all event highlights (admin only)."""
    db = get_database()
    
    # First get all categories to map IDs to names
    categories = {}
    async for cat in db.event_categories.find():
        categories[str(cat["_id"])] = cat.get("name", "")
    
    events = []
    cursor = db.event_highlights.find().sort("order", 1)
    
    async for event in cursor:
        event_data = event_highlight_helper(event)
        event_data["category_name"] = categories.get(event_data["category_id"], "")
        events.append(EventHighlightResponse(**event_data))
    
    return events


@router.post("/event-highlights", response_model=EventHighlightResponse)
async def create_event_highlight(
    event_data: EventHighlightCreate,
    current_user: TokenData = Depends(get_admin_user)
):
    """Create a new event highlight (admin only)."""
    db = get_database()
    
    # Validate category exists
    try:
        category = await db.event_categories.find_one({"_id": ObjectId(event_data.category_id)})
    except:
        raise HTTPException(status_code=400, detail="Invalid category ID")
    
    if not category:
        raise HTTPException(status_code=404, detail="Event category not found")
    
    # Get max order
    max_order_doc = await db.event_highlights.find_one(sort=[("order", -1)])
    next_order = (max_order_doc["order"] + 1) if max_order_doc else 0
    
    event_doc = {
        **event_data.model_dump(),
        "order": event_data.order if event_data.order is not None else next_order,
        "status": "unpublished",
        "date_published": None,
        "last_modified": datetime.utcnow(),
        "created_at": datetime.utcnow(),
    }
    
    result = await db.event_highlights.insert_one(event_doc)
    event_doc["_id"] = result.inserted_id
    
    response_data = event_highlight_helper(event_doc)
    response_data["category_name"] = category.get("name", "")
    
    return EventHighlightResponse(**response_data)


@router.get("/event-highlights/{event_id}", response_model=EventHighlightResponse)
async def get_event_highlight(
    event_id: str,
    current_user: TokenData = Depends(get_admin_user)
):
    """Get a specific event highlight (admin only)."""
    db = get_database()
    
    try:
        event = await db.event_highlights.find_one({"_id": ObjectId(event_id)})
    except:
        raise HTTPException(status_code=400, detail="Invalid event ID")
    
    if not event:
        raise HTTPException(status_code=404, detail="Event highlight not found")
    
    event_data = event_highlight_helper(event)
    
    # Get category name
    try:
        category = await db.event_categories.find_one({"_id": ObjectId(event_data["category_id"])})
        event_data["category_name"] = category.get("name", "") if category else ""
    except:
        event_data["category_name"] = ""
    
    return EventHighlightResponse(**event_data)


@router.put("/event-highlights/{event_id}", response_model=EventHighlightResponse)
async def update_event_highlight(
    event_id: str,
    update_data: EventHighlightUpdate,
    current_user: TokenData = Depends(get_admin_user)
):
    """Update an event highlight (admin only)."""
    db = get_database()
    
    try:
        event = await db.event_highlights.find_one({"_id": ObjectId(event_id)})
    except:
        raise HTTPException(status_code=400, detail="Invalid event ID")
    
    if not event:
        raise HTTPException(status_code=404, detail="Event highlight not found")
    
    # If updating category, validate it exists
    if update_data.category_id:
        try:
            category = await db.event_categories.find_one({"_id": ObjectId(update_data.category_id)})
        except:
            raise HTTPException(status_code=400, detail="Invalid category ID")
        
        if not category:
            raise HTTPException(status_code=404, detail="Event category not found")
    
    # Build update dict
    update_dict = {k: v for k, v in update_data.model_dump().items() if v is not None}
    update_dict["last_modified"] = datetime.utcnow()
    
    # If publishing, set date_published
    if update_data.status == "active" and event.get("status") != "active":
        update_dict["date_published"] = datetime.utcnow()
    
    await db.event_highlights.update_one(
        {"_id": ObjectId(event_id)},
        {"$set": update_dict}
    )
    
    updated_event = await db.event_highlights.find_one({"_id": ObjectId(event_id)})
    event_data = event_highlight_helper(updated_event)
    
    # Get category name
    try:
        category = await db.event_categories.find_one({"_id": ObjectId(event_data["category_id"])})
        event_data["category_name"] = category.get("name", "") if category else ""
    except:
        event_data["category_name"] = ""
    
    return EventHighlightResponse(**event_data)


@router.delete("/event-highlights/{event_id}")
async def delete_event_highlight(
    event_id: str,
    current_user: TokenData = Depends(get_admin_user)
):
    """Delete an event highlight (admin only)."""
    db = get_database()
    
    try:
        result = await db.event_highlights.delete_one({"_id": ObjectId(event_id)})
    except:
        raise HTTPException(status_code=400, detail="Invalid event ID")
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Event highlight not found")
    
    return {"message": "Event highlight deleted"}
