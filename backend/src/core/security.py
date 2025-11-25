from __future__ import annotations

import os
import threading
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import bcrypt
import jwt
from cachetools import TTLCache
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from src.core.config import Settings


# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/v1/auth/login")


ALGORITHM = "HS256"
DEFAULT_ACCESS_TOKEN_EXPIRE_MINUTES = 60


def _get_jwt_secret() -> str:
    secret = os.getenv("JWT_SECRET")
    if not secret:
        raise RuntimeError("JWT_SECRET not configured in environment")
    return secret


def hash_password(plain_password: str) -> str:
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(plain_password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"), hashed_password.encode("utf-8")
        )
    except Exception:
        return False


def create_access_token(
    subject: str,
    expires_delta: Optional[timedelta] = None,
    extra_claims: Optional[Dict[str, Any]] = None,
) -> str:
    if expires_delta is None:
        expires_delta = timedelta(minutes=DEFAULT_ACCESS_TOKEN_EXPIRE_MINUTES)

    now = datetime.now(timezone.utc)
    payload: Dict[str, Any] = {
        "sub": subject,
        "iat": int(now.timestamp()),
        "exp": int((now + expires_delta).timestamp()),
        **(extra_claims or {}),
    }
    return jwt.encode(payload, _get_jwt_secret(), algorithm=ALGORITHM)


def decode_access_token(token: str) -> Dict[str, Any]:
    return jwt.decode(token, _get_jwt_secret(), algorithms=[ALGORITHM])

# Thread-safe user cache with 5-minute TTL
_user_cache = TTLCache(maxsize=1000, ttl=300)
_cache_lock = threading.Lock()


def _get_cached_user(user_id: str):
    """Get user from cache if exists."""
    with _cache_lock:
        return _user_cache.get(user_id)


def _set_cached_user(user_id: str, user):
    """Set user in cache."""
    with _cache_lock:
        _user_cache[user_id] = user


def invalidate_user_cache(user_id: str = None):
    """Invalidate user cache. Call this when user data is updated."""
    with _cache_lock:
        if user_id:
            _user_cache.pop(user_id, None)
        else:
            _user_cache.clear()


async def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    Dependency function that retrieves the current user from the access token.
    Uses caching to avoid database lookups on every request.
    """
    from src.models.user import User
    from src.core.database import SessionLocal
    from src.core.config import Settings

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # For development, allow a mock token to simulate a user
    if Settings.environment == "development" and token == "mock-token-for-development":
        # Create a mock user for development purposes
        class MockUser:
            def __init__(self):
                self.id = "dev-user-123"
                self.email = "dev@example.com"
                self.first_name = "Development"
                self.last_name = "User"

        return MockUser()

    try:
        payload = decode_access_token(token)
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception

        # Check cache first
        cached_user = _get_cached_user(user_id)
        if cached_user is not None:
            return cached_user

        # Fetch from database only if not cached
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if user is None:
                raise credentials_exception
            
            # Cache the user for subsequent requests
            _set_cached_user(user_id, user)
            return user
        finally:
            db.close()
    except jwt.PyJWTError:
        raise credentials_exception


__all__ = [
    "hash_password",
    "verify_password",
    "create_access_token",
    "decode_access_token",
    "get_current_user",
    "invalidate_user_cache",
]
