from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from typing import Optional
from app.config import settings

# Global database client
client: Optional[AsyncIOMotorClient] = None
db: Optional[AsyncIOMotorDatabase] = None


async def connect_to_database():
    """Connect to MongoDB on startup."""
    global client, db
    client = AsyncIOMotorClient(settings.mongodb_url)
    db = client[settings.database_name]
    
    # Create indexes
    await create_indexes()
    
    print(f"Connected to MongoDB: {settings.database_name}")


async def close_database_connection():
    """Close MongoDB connection on shutdown."""
    global client
    if client:
        client.close()
        print("Closed MongoDB connection")


async def create_indexes():
    """Create necessary database indexes."""
    # Users collection indexes
    await db.users.create_index("email", unique=True)
    await db.users.create_index("subdomain", unique=True, sparse=True)
    await db.users.create_index("verification_token", sparse=True)
    
    # Opportunities collection indexes
    await db.opportunities.create_index("status")
    await db.opportunities.create_index("order")
    
    # Websites collection indexes
    await db.websites.create_index("subdomain", unique=True)
    await db.websites.create_index("user_id")
    await db.websites.create_index("status")


def get_database() -> AsyncIOMotorDatabase:
    """Get database instance."""
    return db
