import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Settings(BaseSettings):
    """Application settings."""
    
    # API settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Chef Bot"
    
    # Auth settings
    SECRET_KEY: str = os.getenv("SECRET_KEY", "jK8Hs2Q9zP3tR7xY1vN5bC6aE4dF8gL0mW2nX9pZ3rT7yU6iO1")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "10080"))  # 7 days
    
    # CORS settings
    BACKEND_CORS_ORIGINS: list[str] = [
        "http://localhost",
        "http://localhost:3000",  # React default
        "http://localhost:8000",  # FastAPI default
    ]
    
    # Database settings
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./chef_bot.db")
    
    # DeepSeek API settings
    DEEPSEEK_API_KEY: str = os.getenv("DEEPSEEK_API_KEY", "")
    
    class Config:
        case_sensitive = True


# Create settings instance
settings = Settings()
