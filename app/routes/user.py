from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends
from bson import ObjectId

from app.database import get_database
from app.schemas.website import WebsiteUserUpdate, WebsiteResponse
from app.middleware.auth import get_current_user
from app.schemas.user import TokenData
from app.models.website import website_helper

router = APIRouter()


@router.get("/site", response_model=WebsiteResponse)
async def get_my_site(current_user: TokenData = Depends(get_current_user)):
    """Get current user's website."""
    db = get_database()
    
    site = await db.websites.find_one({"user_id": ObjectId(current_user.user_id)})
    
    if not site:
        raise HTTPException(status_code=404, detail="Website not found")
    
    return WebsiteResponse(**website_helper(site))


@router.put("/site/links", response_model=WebsiteResponse)
async def update_my_site_links(
    update_data: WebsiteUserUpdate,
    current_user: TokenData = Depends(get_current_user)
):
    """Update opportunity button links for user's website.
    
    Customization keys can be:
    - {oppId}_primary: Custom link for primary button
    - {oppId}_secondary: Custom link for secondary button
    """
    db = get_database()
    
    site = await db.websites.find_one({"user_id": ObjectId(current_user.user_id)})
    
    if not site:
        raise HTTPException(status_code=404, detail="Website not found")
    
    if not site.get("can_update_referral", True):
        raise HTTPException(
            status_code=403, 
            detail="You are not allowed to update referral links"
        )
    
    # Validate opportunity IDs exist (extract ID from keys like "id_primary" or "id_secondary")
    for key in update_data.customizations.keys():
        # Parse the key to extract opportunity ID
        if key.endswith('_primary'):
            opp_id = key[:-8]  # Remove '_primary' suffix
        elif key.endswith('_secondary'):
            opp_id = key[:-10]  # Remove '_secondary' suffix
        else:
            opp_id = key  # Legacy format - just the ID
        
        try:
            opp = await db.opportunities.find_one({"_id": ObjectId(opp_id)})
            if not opp:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Invalid opportunity ID: {opp_id}"
                )
        except Exception:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid opportunity ID format: {opp_id}"
            )
    
    # Merge with existing customizations
    existing_customizations = site.get("customizations", {})
    merged_customizations = {**existing_customizations, **update_data.customizations}
    
    await db.websites.update_one(
        {"_id": site["_id"]},
        {
            "$set": {
                "customizations": merged_customizations,
                "last_modified": datetime.utcnow()
            }
        }
    )
    
    updated_site = await db.websites.find_one({"_id": site["_id"]})
    return WebsiteResponse(**website_helper(updated_site))


@router.delete("/site/links/{link_key}")
async def remove_custom_link(
    link_key: str,
    current_user: TokenData = Depends(get_current_user)
):
    """Remove a custom link for an opportunity.
    
    link_key can be:
    - {oppId}_primary: Remove primary button custom link
    - {oppId}_secondary: Remove secondary button custom link
    - {oppId}: Legacy format - remove the custom link
    """
    db = get_database()
    
    site = await db.websites.find_one({"user_id": ObjectId(current_user.user_id)})
    
    if not site:
        raise HTTPException(status_code=404, detail="Website not found")
    
    customizations = site.get("customizations", {})
    
    if link_key in customizations:
        del customizations[link_key]
        
        await db.websites.update_one(
            {"_id": site["_id"]},
            {
                "$set": {
                    "customizations": customizations,
                    "last_modified": datetime.utcnow()
                }
            }
        )
    
    return {"message": "Custom link removed"}
