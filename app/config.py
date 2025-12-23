from pydantic_settings import BaseSettings
from typing import List
from functools import lru_cache


class Settings(BaseSettings):
    # MongoDB
    mongodb_url: str = "mongodb://localhost:27017"
    database_name: str = "uigisc"
    
    # JWT
    secret_key: str = "your-secret-key-change-in-production-min-32-chars"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440  # 24 hours
    
    # Admin
    admin_emails: str = "admin@uigisc.com"
    
    # Email
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    email_from: str = "noreply@uigisc.com"
    
    # Frontend
    frontend_url: str = "http://localhost:5173"
    allowed_origins: str = "http://localhost:5173,http://localhost:3000,https://uigsc.vercel.app"
    
    # Environment
    environment: str = "development"
    
    # DigitalOcean Spaces
    dospace_secret: str = ""
    dospace_access_key: str = ""
    dospace_endpoint: str = ""
    dospace_bucket_name: str = ""

    @property
    def do_secret(self) -> str:
        return self.dospace_secret
    
    @property
    def do_access_key(self) -> str:
        return self.dospace_access_key
    
    @property
    def do_endpoint(self) -> str:
        return self.dospace_endpoint
    
    @property
    def do_bucket(self) -> str:
        return self.dospace_bucket_name
    
    @property
    def admin_email_list(self) -> List[str]:
        return [email.strip() for email in self.admin_emails.split(",")]
    
    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
