from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Optional

# Load environment variables from a .env file if available
try:
    from dotenv import load_dotenv  # type: ignore

    load_dotenv()
except Exception:
    # Optional dependency; safe to ignore if not installed
    pass


@dataclass(frozen=True)
class Settings:
    # App
    app_name: str = os.getenv("APP_NAME", "Financial Assistant API")
    environment: str = os.getenv("ENV", os.getenv("ENVIRONMENT", "development"))
    log_level: str = os.getenv("LOG_LEVEL", "INFO")

    # Supabase
    supabase_url: str = os.getenv("SUPABASE_URL", "")
    supabase_anon_key: str = os.getenv("SUPABASE_ANON_KEY", "")
    supabase_service_role_key: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

    # Security
    jwt_secret: str = os.getenv("JWT_SECRET", "")
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

    # AI
    google_api_key: str = os.getenv("GOOGLE_API_KEY", "")
    
    # File Uploads
    upload_dir: str = os.getenv("UPLOAD_DIR", "uploads")


# Global settings instance
settings = Settings()


def configure_logging(level_name: Optional[str] = None) -> None:
    level_str = (level_name or Settings.log_level).upper()
    level = getattr(logging, level_str, logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )


__all__ = ["Settings", "configure_logging"]


