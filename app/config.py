import os
import shutil
from pathlib import Path
from pydantic import BaseModel
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

IS_VERCEL = bool(os.getenv("VERCEL") or os.getenv("VERCEL_ENV") or os.getenv("AWS_LAMBDA_FUNCTION_NAME"))

class Settings(BaseModel):
    APP_NAME: str = os.getenv("APP_NAME", "TrendBlogo")
    APP_ENV: str = os.getenv("APP_ENV", "development")
    APP_SECRET: str = os.getenv("APP_SECRET", "trendblogo-secure-random-token-2026")
    BASE_URL: str = os.getenv("BASE_URL", "http://localhost:8000")
    
    # On Vercel, the only writable location is /tmp
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:////tmp/trendblogo.db" if IS_VERCEL else "sqlite:///./trendblogo.db")
    
    ADMIN_EMAIL: str = os.getenv("ADMIN_EMAIL", "admin@trendblogo.com")
    ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "Admin123!")
    
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    IMAGE_GENERATION_PROVIDER: str = os.getenv("IMAGE_GENERATION_PROVIDER", "auto")
    DALL_E_MODEL: str = os.getenv("DALL_E_MODEL", "dall-e-3")
    
    DEFAULT_WORD_COUNT: int = int(os.getenv("DEFAULT_WORD_COUNT", "1500"))
    MAX_DAILY_GENERATIONS: int = int(os.getenv("MAX_DAILY_GENERATIONS", "100"))
    ENABLE_QUALITY_CONTROL: bool = os.getenv("ENABLE_QUALITY_CONTROL", "true").lower() == "true"
    AUTO_SCHEDULE_INTERVAL_HOURS: int = int(os.getenv("AUTO_SCHEDULE_INTERVAL_HOURS", "6"))
    
    IS_VERCEL: bool = IS_VERCEL
    BASE_DIR: Path = BASE_DIR
    STATIC_DIR: Path = BASE_DIR / "app" / "static"
    TEMPLATES_DIR: Path = BASE_DIR / "app" / "templates"
    UPLOADS_DIR: Path = Path("/tmp/uploads") if IS_VERCEL else BASE_DIR / "app" / "static" / "uploads"

settings = Settings()

# Safe initialization of directories
try:
    os.makedirs(settings.UPLOADS_DIR, exist_ok=True)
    if settings.IS_VERCEL:
        bundled_uploads = settings.STATIC_DIR / "uploads"
        if bundled_uploads.exists():
            for item in bundled_uploads.glob("*"):
                target_item = settings.UPLOADS_DIR / item.name
                if not target_item.exists() and item.is_file():
                    try:
                        shutil.copy2(item, target_item)
                    except Exception:
                        pass
except Exception as e:
    print(f"Directory initialization notice: {e}")
