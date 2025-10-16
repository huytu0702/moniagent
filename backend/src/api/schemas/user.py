from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    password: str  # Plain text password for creation


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserRead(BaseModel):
    id: str
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime


__all__ = ["UserCreate", "UserLogin", "UserRead"]