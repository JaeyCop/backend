import os
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "Recipe Scraper API"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = False
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-super-secret-key-change-this-in-production")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ALGORITHM: str = "HS256"
    SUPABASE_JWT_SECRET: str = os.getenv("SUPABASE_JWT_SECRET", "")
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/dbname")
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20
    
    # External APIs
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    YOUTUBE_API_KEY: Optional[str] = os.getenv("YOUTUBE_API_KEY")
    
    # Redis/Cache (removed for Fly.io optimization)
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    
    # CORS
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:3001,http://localhost:8080,https://3001-jaeycop-backend-slvp87wka7t.ws-eu120.gitpod.io,https://8000-jaeycop-backend-slvp87wka7t.ws-eu120.gitpod.io,https://3000-jaeycop-backend-slvp87wka7t.ws-eu120.gitpod.io"
    
    @property
    def allowed_origins_list(self) -> list[str]:
        """Convert ALLOWED_ORIGINS string to list."""
        if isinstance(self.ALLOWED_ORIGINS, str):
            return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]
        return self.ALLOWED_ORIGINS
    
    # Email (for password reset)
    SMTP_HOST: Optional[str] = os.getenv("SMTP_HOST")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USERNAME: Optional[str] = os.getenv("SMTP_USERNAME")
    SMTP_PASSWORD: Optional[str] = os.getenv("SMTP_PASSWORD")
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    class Config:
        # Look for .env file in the parent directory (workspace root)
        env_file = Path(__file__).parent.parent.parent.parent / ".env"
        case_sensitive = True


settings = Settings()
