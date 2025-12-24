from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from bson import ObjectId


class PyObjectId(ObjectId):
    """Custom ObjectId type for Pydantic models."""
    
    @classmethod
    def __get_validators__(cls):
        yield cls.validate
    
    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)
    
    @classmethod
    def __get_pydantic_json_schema__(cls, field_schema):
        field_schema.update(type="string")


class UserModel(BaseModel):
    """User database model."""
    id: Optional[str] = Field(default=None, alias="_id")
    email: str
    password_hash: str
    subdomain: Optional[str] = None
    name: Optional[str] = None
    mobile: Optional[str] = None
    role: str = "user"  # "admin" or "user"
    is_verified: bool = False
    verification_token: Optional[str] = None
    verification_token_expires: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: str}


class UserInDB(UserModel):
    """User model as stored in database."""
    pass


def user_helper(user: dict) -> dict:
    """Convert MongoDB user document to dict."""
    return {
        "id": str(user["_id"]),
        "email": user["email"],
        "subdomain": user.get("subdomain"),
        "name": user.get("name"),
        "mobile": user.get("mobile"),
        "role": user.get("role", "user"),
        "is_verified": user.get("is_verified", False),
        "created_at": user.get("created_at"),
        "updated_at": user.get("updated_at"),
    }
