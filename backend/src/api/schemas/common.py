from __future__ import annotations

from typing import Optional, List, Any
from datetime import datetime

from pydantic import BaseModel, Field


class MessageResponse(BaseModel):
    message: str


class HealthResponse(BaseModel):
    status: str = "healthy"


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class PaginatedResponse(BaseModel):
    """Generic paginated response for list endpoints."""

    items: List[Any] = Field(..., description="Array of items returned")
    total: int = Field(..., description="Total number of items available")
    skip: int = Field(default=0, description="Number of items skipped")
    limit: int = Field(default=20, description="Number of items returned")

    class Config:
        schema_extra = {
            "example": {
                "items": [{"id": "uuid", "name": "Example"}],
                "total": 42,
                "skip": 0,
                "limit": 20,
            }
        }


class ErrorResponse(BaseModel):
    """Standard error response schema."""

    detail: str = Field(..., description="Human-readable error message")
    error_code: str = Field(..., description="Machine-readable error code")

    class Config:
        schema_extra = {
            "example": {
                "detail": "User not found",
                "error_code": "NOT_FOUND",
            }
        }


class SuccessResponse(BaseModel):
    """Standard success response wrapper."""

    success: bool = Field(default=True, description="Whether operation was successful")
    message: Optional[str] = Field(None, description="Optional success message")
    data: Optional[Any] = Field(None, description="Response data")

    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "message": "Operation completed successfully",
                "data": {},
            }
        }


class TimestampedModel(BaseModel):
    """Base model for resources with timestamps."""

    created_at: datetime = Field(..., description="When the resource was created")
    updated_at: Optional[datetime] = Field(
        None, description="When the resource was last updated"
    )

    class Config:
        schema_extra = {
            "example": {
                "created_at": "2025-01-15T10:30:00Z",
                "updated_at": "2025-01-15T11:00:00Z",
            }
        }


class UserReference(BaseModel):
    """Reference to a user."""

    id: str = Field(..., description="User ID")
    email: str = Field(..., description="User email")
    first_name: str = Field(..., description="User first name")
    last_name: str = Field(..., description="User last name")

    class Config:
        schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "email": "user@example.com",
                "first_name": "John",
                "last_name": "Doe",
            }
        }


class CurrencyAmount(BaseModel):
    """Monetary amount in USD."""

    amount: float = Field(
        ..., ge=0, description="Amount in USD (non-negative, 2 decimal places)"
    )
    currency: str = Field(default="USD", description="Currency code (ISO 4217)")

    class Config:
        schema_extra = {"example": {"amount": 25.50, "currency": "USD"}}


class ConfidenceScore(BaseModel):
    """Confidence score with interpretation."""

    score: float = Field(
        ..., ge=0, le=1, description="Confidence score between 0 and 1"
    )
    interpretation: str = Field(
        ..., description="Human-readable interpretation (low/medium/high)"
    )

    class Config:
        schema_extra = {"example": {"score": 0.92, "interpretation": "high"}}


__all__ = [
    "MessageResponse",
    "HealthResponse",
    "TokenResponse",
    "ErrorResponse",
]
