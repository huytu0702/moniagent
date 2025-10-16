from __future__ import annotations

import os
from functools import lru_cache
from typing import Optional, AsyncGenerator

from supabase import Client, create_client
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import create_engine
from contextlib import contextmanager, asynccontextmanager

# SQLAlchemy Base class for ORM models
Base = declarative_base()

# Initialize database engine and session (for standard database models, separate from Supabase)
# Option 1: Use DATABASE_URL if provided directly
# Option 2: Build from Supabase credentials
DATABASE_URL = os.getenv("DATABASE_URL", "")

if not DATABASE_URL:
    # Build PostgreSQL connection string from Supabase credentials
    SUPABASE_URL = os.getenv("SUPABASE_URL", "")
    SUPABASE_DB_PASSWORD = os.getenv("SUPABASE_DB_PASSWORD", "")

    if SUPABASE_URL and SUPABASE_DB_PASSWORD:
        import re

        match = re.search(r'https://([^.]+)\.supabase\.co', SUPABASE_URL)
        if match:
            project_ref = match.group(1)
            # Supabase PostgreSQL connection string format (Pooler mode for better performance)
            DATABASE_URL = f"postgresql://postgres.{project_ref}:{SUPABASE_DB_PASSWORD}@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres"
        else:
            DATABASE_URL = "sqlite:///./test.db"
    else:
        DATABASE_URL = "sqlite:///./test.db"  # Fallback to SQLite

# Add connection args for PostgreSQL
if DATABASE_URL.startswith("postgresql"):
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,  # Verify connections before using them
        echo=True,  # Log SQL queries for debugging
    )
else:
    engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """
    Dependency function that provides database sessions for FastAPI endpoints.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class DatabaseConfig:
    """
    Simple environment-driven configuration for Supabase.
    Prefers service role key for server-side access; falls back to anon key.
    """

    def __init__(self) -> None:
        self.url: str = os.getenv("SUPABASE_URL", "")
        # Prefer service role key for backend operations; fallback to anon for read-only scenarios
        self.key: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv(
            "SUPABASE_ANON_KEY", ""
        )

        if not self.url or not self.key:
            raise RuntimeError(
                "Supabase configuration missing: ensure SUPABASE_URL and key env vars are set"
            )


@lru_cache(maxsize=1)
def get_supabase_client() -> Client:
    """Create (once) and return a Supabase client configured from environment."""
    cfg = DatabaseConfig()
    return create_client(cfg.url, cfg.key)


def users_table() -> Client.table:
    """Convenience accessor for the users table."""
    return get_supabase_client().table("users")


__all__ = ["get_supabase_client", "users_table", "DatabaseConfig"]
