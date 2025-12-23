from datetime import datetime
from typing import List
from fastapi import APIRouter, HTTPException, status, Depends, File, UploadFile
from bson import ObjectId

from app.database import get_database
from app.schemas.opportunity import (
    OpportunityCreate, OpportunityUpdate, OpportunityResponse
)
from app.schemas.website import WebsiteUpdate, WebsiteResponse
from app.middleware.auth import get_admin_user
from app.schemas.user import TokenData
from app.models.opportunity import opportunity_helper
from app.models.website import website_helper
from app.services.storage import storage_service

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
