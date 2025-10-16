from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class MessageResponse(BaseModel):
    message: str


class HealthResponse(BaseModel):
    status: str = "healthy"


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ErrorResponse(BaseModel):
    detail: str
    code: Optional[str] = None


__all__ = [
    "MessageResponse",
    "HealthResponse",
    "TokenResponse",
    "ErrorResponse",
]


