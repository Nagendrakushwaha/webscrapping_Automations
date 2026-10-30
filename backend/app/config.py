import os
from pathlib import Path
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
EXPORT_DIR = DATA_DIR / "exports"

DATA_DIR.mkdir(parents=True, exist_ok=True)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
EXPORT_DIR.mkdir(parents=True, exist_ok=True)

class Settings(BaseSettings):
    APP_NAME: str = "AI LEAD INTELLIGENCE"
    APP_VERSION: str = "1.0.0"
    COMPANY_NAME: str = "Tex Web Solutions Pvt. Ltd."
    COMPANY_SERVICES: list[str] = [
        "Website Design",
        "Website Development",
        "Website Redesign",
        "Web Applications",
        "SEO",
        "Digital Solutions"
    ]
    
    # Database
    DATABASE_URL: str = f"sqlite+aiosqlite:///{DATA_DIR / 'leads.db'}"
    SYNC_DATABASE_URL: str = f"sqlite:///{DATA_DIR / 'leads.db'}"
    
    # API Keys (loaded from env or UI settings)
    OPENAI_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    TAVILY_API_KEY: str = ""
    GOOGLE_SEARCH_API_KEY: str = ""
    GOOGLE_SEARCH_CX: str = ""
    GOOGLE_PLACES_API_KEY: str = ""
    BING_SEARCH_API_KEY: str = ""
    BRAVE_SEARCH_API_KEY: str = ""
    APOLLO_API_KEY: str = ""
    HUNTER_API_KEY: str = ""
    
    # Worker settings
    DEFAULT_CONCURRENCY: int = 3
    REQUEST_TIMEOUT: int = 15
    USER_AGENT: str = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36 AILeadIntelligence/1.0"
    )

    class Config:
        env_file = ".env"
        extra = "allow"

settings = Settings()
