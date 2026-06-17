import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "BARAKA API"
    # Vercel Postgres URL-ni qo'llab-quvvatlaymiz
    _db_url: str = os.getenv("POSTGRES_URL", os.getenv("DATABASE_URL", "sqlite:///./baraka.db"))
    if _db_url.startswith("postgres://"):
        _db_url = _db_url.replace("postgres://", "postgresql://", 1)
    
    SQLALCHEMY_DATABASE_URI: str = _db_url
    SECRET_KEY: str = os.getenv("SECRET_KEY", "SUPER_SECRET_KEY_FOR_BARAKA_DEVELOPMENT")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

settings = Settings()
