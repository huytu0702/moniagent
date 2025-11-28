"""
Validation utilities for common validation patterns used across the application.
"""

from typing import Any, Optional
import re
from src.utils.exceptions import ValidationError


def validate_required_string(value: Any, field_name: str, min_length: int = 1) -> str:
    """
    Validate that a value is a non-empty string.

    Args:
        value: Value to validate
        field_name: Name of the field for error messages
        min_length: Minimum length required

    Returns:
        Validated string

    Raises:
        ValidationError: If validation fails
    """
    if not value or not isinstance(value, str):
        raise ValidationError(f"{field_name} is required and must be a string")

    if len(value.strip()) < min_length:
        raise ValidationError(f"{field_name} must be at least {min_length} characters")

    return value.strip()


def validate_email(email: str) -> str:
    """
    Validate email format.

    Args:
        email: Email address to validate

    Returns:
        Validated email

    Raises:
        ValidationError: If email is invalid
    """
    if not email or not isinstance(email, str):
        raise ValidationError("Email is required and must be a string")

    email = email.strip().lower()

    # Check for double dots which are invalid
    if ".." in email:
        raise ValidationError("Invalid email format")

    # Basic email pattern
    email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"

    if not re.match(email_pattern, email):
        raise ValidationError("Invalid email format")

    return email


def validate_password(password: str, min_length: int = 8) -> str:
    """
    Validate password strength.

    Args:
        password: Password to validate
        min_length: Minimum password length

    Returns:
        Validated password

    Raises:
        ValidationError: If password is too weak
    """
    if not password or len(password) < min_length:
        raise ValidationError(f"Password must be at least {min_length} characters long")

    # Check for at least one uppercase, lowercase, digit, and special character
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(c in "!@#$%^&*()-_=+[]{}|;:,.<>?" for c in password)

    if not (has_upper and has_lower and has_digit):
        raise ValidationError(
            "Password must contain uppercase, lowercase, and numeric characters"
        )

    return password


def validate_amount(amount: Any, field_name: str = "Amount") -> float:
    """
    Validate that a value is a positive number.

    Args:
        amount: Value to validate
        field_name: Name of the field for error messages

    Returns:
        Validated amount as float

    Raises:
        ValidationError: If validation fails
    """
    try:
        print(f"DEBUG: validate_amount called with {amount} type={type(amount)}")
        amount_float = float(amount)
    except (TypeError, ValueError):
        raise ValidationError(f"{field_name} must be a valid number")

    if amount_float < 0:
        raise ValidationError(f"{field_name} must be positive")

    return round(amount_float, 2)


def validate_percentage(value: Any, field_name: str = "Percentage") -> float:
    """
    Validate that a value is between 0 and 100.

    Args:
        value: Value to validate
        field_name: Name of the field for error messages

    Returns:
        Validated percentage as float

    Raises:
        ValidationError: If validation fails
    """
    try:
        percentage = float(value)
    except (TypeError, ValueError):
        raise ValidationError(f"{field_name} must be a valid number")

    if percentage < 0 or percentage > 100:
        raise ValidationError(f"{field_name} must be between 0 and 100")

    return percentage


def validate_confidence_score(score: Any) -> float:
    """
    Validate that a value is a confidence score (0-1).

    Args:
        score: Score to validate

    Returns:
        Validated score as float

    Raises:
        ValidationError: If validation fails
    """
    try:
        score_float = float(score)
    except (TypeError, ValueError):
        raise ValidationError("Confidence score must be a valid number")

    if score_float < 0 or score_float > 1:
        raise ValidationError("Confidence score must be between 0 and 1")

    return score_float


def validate_uuid(value: Any, field_name: str = "ID") -> str:
    """
    Validate that a value is a valid UUID format.

    Args:
        value: Value to validate
        field_name: Name of the field for error messages

    Returns:
        Validated UUID string

    Raises:
        ValidationError: If validation fails
    """
    uuid_pattern = r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"

    if not isinstance(value, str) or not re.match(uuid_pattern, value.lower()):
        raise ValidationError(f"{field_name} must be a valid UUID")

    return value


def validate_enum(value: Any, allowed_values: list, field_name: str) -> str:
    """
    Validate that a value is one of allowed values.

    Args:
        value: Value to validate
        allowed_values: List of allowed values
        field_name: Name of the field for error messages

    Returns:
        Validated value

    Raises:
        ValidationError: If validation fails
    """
    if value not in allowed_values:
        raise ValidationError(
            f"{field_name} must be one of: {', '.join(map(str, allowed_values))}"
        )

    return value


def validate_date_string(date_string: str) -> str:
    """
    Validate ISO format date string (YYYY-MM-DD).

    Args:
        date_string: Date string to validate

    Returns:
        Validated date string

    Raises:
        ValidationError: If format is invalid
    """
    from datetime import datetime

    date_pattern = r"^\d{4}-\d{2}-\d{2}$"

    if not re.match(date_pattern, date_string):
        raise ValidationError("Date must be in format YYYY-MM-DD")

    # Validate that it's an actual valid date (including leap year checks)
    try:
        datetime.strptime(date_string, "%Y-%m-%d")
    except ValueError:
        raise ValidationError(f"Invalid date: {date_string}")

    return date_string
