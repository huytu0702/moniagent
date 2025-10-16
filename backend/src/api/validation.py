"""
Input validation and sanitization middleware for API endpoints.
Implements centralized validation and security sanitization.
"""

from typing import Any, Dict, Optional, List
import re
from pydantic import BaseModel, validator, field_validator
from src.utils.exceptions import ValidationError


class PaginationRequest(BaseModel):
    """Request schema for paginated endpoints"""

    limit: int = 10
    offset: int = 0

    @field_validator("limit")
    @classmethod
    def validate_limit(cls, v: int) -> int:
        """Validate pagination limit"""
        if v < 1 or v > 100:
            raise ValueError("Limit must be between 1 and 100")
        return v

    @field_validator("offset")
    @classmethod
    def validate_offset(cls, v: int) -> int:
        """Validate pagination offset"""
        if v < 0:
            raise ValueError("Offset must be non-negative")
        return v


class ChatMessageRequest(BaseModel):
    """Request schema for chat messages"""

    content: str
    session_id: str
    message_type: str = "text"  # text, image, etc.

    @field_validator("content")
    @classmethod
    def validate_content(cls, v: str) -> str:
        """Sanitize and validate message content"""
        if not v or len(v.strip()) == 0:
            raise ValueError("Message content cannot be empty")
        if len(v) > 10000:
            raise ValueError("Message content too long (max 10000 characters)")
        return v.strip()

    @field_validator("session_id")
    @classmethod
    def validate_session_id(cls, v: str) -> str:
        """Validate session ID format"""
        if not re.match(r"^[a-f0-9\-]+$", v):
            raise ValueError("Invalid session ID format")
        return v

    @field_validator("message_type")
    @classmethod
    def validate_message_type(cls, v: str) -> str:
        """Validate message type"""
        allowed_types = ["text", "image", "file"]
        if v not in allowed_types:
            raise ValueError(f"Message type must be one of: {allowed_types}")
        return v


class ExpenseExtractionRequest(BaseModel):
    """Request schema for expense extraction"""

    price: float
    location: str
    date: Optional[str] = None
    category_id: str
    description: Optional[str] = None

    @field_validator("price")
    @classmethod
    def validate_price(cls, v: float) -> float:
        """Validate expense amount"""
        if v <= 0:
            raise ValueError("Price must be positive")
        if v > 1000000:
            raise ValueError("Price exceeds maximum allowed amount")
        return round(v, 2)

    @field_validator("location")
    @classmethod
    def validate_location(cls, v: str) -> str:
        """Sanitize location field"""
        if not v or len(v.strip()) == 0:
            raise ValueError("Location cannot be empty")
        if len(v) > 500:
            raise ValueError("Location too long (max 500 characters)")
        return v.strip()

    @field_validator("date")
    @classmethod
    def validate_date(cls, v: Optional[str]) -> Optional[str]:
        """Validate date format (YYYY-MM-DD)"""
        if v is None:
            return v
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", v):
            raise ValueError("Date must be in format YYYY-MM-DD")
        return v

    @field_validator("category_id")
    @classmethod
    def validate_category_id(cls, v: str) -> str:
        """Validate category ID format"""
        if not re.match(r"^[a-f0-9\-]+$", v):
            raise ValueError("Invalid category ID format")
        return v

    @field_validator("description")
    @classmethod
    def validate_description(cls, v: Optional[str]) -> Optional[str]:
        """Sanitize description field"""
        if v is None:
            return v
        if len(v) > 1000:
            raise ValueError("Description too long (max 1000 characters)")
        return v.strip()


class FileUploadRequest(BaseModel):
    """Request schema for file uploads"""

    filename: str
    file_size: int
    mime_type: str

    @field_validator("filename")
    @classmethod
    def validate_filename(cls, v: str) -> str:
        """Sanitize filename"""
        # Remove path traversal attempts
        v = v.replace("../", "").replace("..\\", "")
        # Allow only alphanumeric, dots, hyphens, underscores
        if not re.match(r"^[a-zA-Z0-9._\-]+$", v):
            raise ValueError("Invalid filename format")
        return v

    @field_validator("file_size")
    @classmethod
    def validate_file_size(cls, v: int) -> int:
        """Validate file size (max 10MB)"""
        max_size = 10 * 1024 * 1024  # 10MB
        if v <= 0 or v > max_size:
            raise ValueError(f"File size must be between 1 byte and {max_size} bytes")
        return v

    @field_validator("mime_type")
    @classmethod
    def validate_mime_type(cls, v: str) -> str:
        """Validate MIME type"""
        allowed_types = [
            "image/jpeg",
            "image/png",
            "image/gif",
            "image/webp",
            "application/pdf",
        ]
        if v not in allowed_types:
            raise ValueError(f"MIME type must be one of: {allowed_types}")
        return v


class BudgetRequest(BaseModel):
    """Request schema for budget operations"""

    category_id: str
    monthly_limit: float
    currency: str = "USD"

    @field_validator("category_id")
    @classmethod
    def validate_category_id(cls, v: str) -> str:
        """Validate category ID"""
        if not re.match(r"^[a-f0-9\-]+$", v):
            raise ValueError("Invalid category ID format")
        return v

    @field_validator("monthly_limit")
    @classmethod
    def validate_monthly_limit(cls, v: float) -> float:
        """Validate monthly budget limit"""
        if v <= 0:
            raise ValueError("Monthly limit must be positive")
        if v > 1000000:
            raise ValueError("Monthly limit exceeds maximum allowed amount")
        return round(v, 2)

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        """Validate currency code"""
        # Allow common currency codes
        valid_currencies = ["USD", "EUR", "GBP", "JPY", "AUD", "CAD", "VND"]
        if v.upper() not in valid_currencies:
            raise ValueError(f"Currency must be one of: {valid_currencies}")
        return v.upper()


# ===== Sanitization Utilities =====


def sanitize_text(text: str, max_length: int = 1000) -> str:
    """
    Sanitize text input by removing potentially harmful content.

    Args:
        text: Text to sanitize
        max_length: Maximum allowed length

    Returns:
        Sanitized text
    """
    if not isinstance(text, str):
        return ""

    # Remove leading/trailing whitespace
    text = text.strip()

    # Remove control characters
    text = "".join(char for char in text if ord(char) >= 32 or char in "\n\t")

    # Truncate if too long
    if len(text) > max_length:
        text = text[: max_length - 3] + "..."

    return text


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename by removing invalid characters.

    Args:
        filename: Filename to sanitize

    Returns:
        Sanitized filename
    """
    # Remove path traversal attempts
    filename = filename.replace("../", "").replace("..\\", "")

    # Remove invalid characters
    filename = re.sub(r"[^a-zA-Z0-9._\-]", "_", filename)

    # Limit length
    if len(filename) > 255:
        name, ext = filename.rsplit(".", 1) if "." in filename else (filename, "")
        name = name[: 251 - len(ext)]
        filename = f"{name}.{ext}" if ext else name

    return filename


def validate_request_fields(
    data: Dict[str, Any], required_fields: List[str], optional_fields: List[str] = None
) -> bool:
    """
    Validate that required and optional fields are present.

    Args:
        data: Request data dictionary
        required_fields: List of required field names
        optional_fields: List of optional field names

    Returns:
        True if validation passes

    Raises:
        ValidationError: If validation fails
    """
    optional_fields = optional_fields or []

    # Check required fields
    for field in required_fields:
        if field not in data or data[field] is None:
            raise ValidationError(f"Required field '{field}' is missing")

    # Check for unexpected fields
    allowed_fields = set(required_fields + optional_fields)
    provided_fields = set(data.keys())
    unexpected = provided_fields - allowed_fields

    if unexpected:
        raise ValidationError(f"Unexpected fields: {', '.join(unexpected)}")

    return True


__all__ = [
    "PaginationRequest",
    "ChatMessageRequest",
    "ExpenseExtractionRequest",
    "FileUploadRequest",
    "BudgetRequest",
    "sanitize_text",
    "sanitize_filename",
    "validate_request_fields",
]
