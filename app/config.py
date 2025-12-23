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
    
    # Environment
    environment: str = "development"
    
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
