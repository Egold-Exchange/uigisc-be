"""
Seed script to initialize the database with admin user and sample opportunities.
Run with: python -m app.seed
"""
import asyncio
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient

from app.config import settings
from app.services.auth import get_password_hash


async def seed_database():
    """Seed the database with initial data."""
    client = AsyncIOMotorClient(settings.mongodb_url)
    db = client[settings.database_name]
    
    print(f"Seeding database: {settings.database_name}")
    
    # Create indexes
    await db.users.create_index("email", unique=True)
    await db.users.create_index("subdomain", unique=True, sparse=True)
    await db.opportunities.create_index("status")
    await db.opportunities.create_index("order")
    await db.websites.create_index("subdomain", unique=True)
    await db.websites.create_index("user_id")
    
    # Check if admin exists
    admin_exists = await db.users.find_one({"email": "admin@uigisc.com"})
    
    if not admin_exists:
        # Create admin user
        admin_doc = {
            "email": "admin@uigisc.com",
            "password_hash": get_password_hash("12345678"),
            "subdomain": None,
            "role": "admin",
            "is_verified": True,
            "verification_token": None,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
        
        await db.users.insert_one(admin_doc)
        print("✓ Created admin user (admin@uigisc.com / 12345678)")
    else:
        print("→ Admin user already exists")
    
    # Check if sample opportunities exist
    opp_count = await db.opportunities.count_documents({})
    
    if opp_count == 0:
        # Create sample opportunities matching the frontend
        sample_opportunities = [
            {
                "name": "Bitnest",
                "image": "",
                "description": "Learn more about Bitnest and how it can help you grow within the UIGISC community.",
                "videos": [{"title": "Bitnest", "vimeo_id": "1030432292"}],
                "bottom_description": "",
                "telegram_link": None,
                "primary_button": {"text": "Get Started", "link": "#"},
                "secondary_button": {"text": "Learn More", "link": "#"},
                "status": "active",
                "is_featured": False,
                "order": 1,
                "date_published": datetime.utcnow(),
                "last_modified": datetime.utcnow(),
                "created_at": datetime.utcnow(),
            },
            {
                "name": "OlyLife",
                "image": "",
                "description": "Learn more about OlyLife and how it can help you grow within the UIGISC community.",
                "videos": [{"title": "OlyLife", "vimeo_id": "1030432292"}],
                "bottom_description": "",
                "telegram_link": None,
                "primary_button": {"text": "Get Started", "link": "#"},
                "secondary_button": {"text": "Learn More", "link": "#"},
                "status": "active",
                "is_featured": False,
                "order": 2,
                "date_published": datetime.utcnow(),
                "last_modified": datetime.utcnow(),
                "created_at": datetime.utcnow(),
            },
            {
                "name": "Reach Solar",
                "image": "",
                "description": "Over the past decade, the solar industry has undergone transformational changes, all of which benefit the homeowner and consumer. Still, choosing solar savings is an important and impactful decision. Here at REACH Solar, we pride ourselves on educating and empowering our clients; offering comprehensive resources and transparent responses to your questions.",
                "videos": [
                    {"title": "THE SUN", "vimeo_id": "1030432292"},
                    {"title": "MAKE MONEY WITH REACH", "vimeo_id": "1030432292"},
                    {"title": "CEO Welcome Message & Overview", "vimeo_id": "1030432292"}
                ],
                "bottom_description": "",
                "telegram_link": "https://t.me/+Rf0LShUOiVw5ZWYx",
                "primary_button": {"text": "COPY THIS LINK TO MAKE MONEY WITH REACH!", "link": "https://t.me/+Rf0LShUOiVw5ZWYx"},
                "secondary_button": {"text": "CLICK HERE TO GET SOLAR!", "link": "#"},
                "status": "active",
                "is_featured": False,
                "order": 5,
                "date_published": datetime.utcnow(),
                "last_modified": datetime.utcnow(),
                "created_at": datetime.utcnow(),
            },
            {
                "name": "Xtrends",
                "image": "",
                "description": "Built on Solana, turns social trends into tradable coins for creators, traders, and investors.",
                "videos": [{"title": "Xtrends", "vimeo_id": "1030432292"}],
                "bottom_description": "",
                "telegram_link": None,
                "primary_button": {"text": "Learn More", "link": "#"},
                "secondary_button": {"text": "Get Started", "link": "#"},
                "status": "active",
                "is_featured": True,
                "order": 0,
                "date_published": datetime.utcnow(),
                "last_modified": datetime.utcnow(),
                "created_at": datetime.utcnow(),
            },
        ]
        
        await db.opportunities.insert_many(sample_opportunities)
        print(f"✓ Created {len(sample_opportunities)} sample opportunities")
    else:
        print(f"→ {opp_count} opportunities already exist")
    
    client.close()
    print("\nSeeding complete!")


if __name__ == "__main__":
    asyncio.run(seed_database())
