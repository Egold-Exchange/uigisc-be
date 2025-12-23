from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import settings
from app.database import connect_to_database, close_database_connection
from app.routes import auth, admin, public, user


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle - startup and shutdown events."""
    # Startup
    await connect_to_database()
    yield
    # Shutdown
    await close_database_connection()


app = FastAPI(
    title="UIGISC API",
    description="Backend API for UIGISC platform",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
origins = [origin.strip() for origin in settings.allowed_origins.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex="https://uigsc-.*\.vercel\.app",  # Support for Vercel preview/branch deployments
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])
app.include_router(public.router, prefix="/api", tags=["Public"])
app.include_router(user.router, prefix="/api/user", tags=["User"])


@app.get("/")
async def root():
    return {
        "message": "UIGISC API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
