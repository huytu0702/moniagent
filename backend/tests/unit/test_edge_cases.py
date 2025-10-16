"""
Unit tests for edge cases and error handling scenarios.
"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta
from uuid import uuid4

from src.utils.validators import (
    validate_required_string,
    validate_email,
    validate_password,
    validate_amount,
    validate_percentage,
    validate_confidence_score,
)
from src.utils.exceptions import ValidationError


class TestValidationFunctions:
    """Test validation utilities for edge cases."""

    def test_validate_required_string_empty(self):
        """Test that empty string raises error."""
        with pytest.raises(ValidationError):
            validate_required_string("", "test_field")

    def test_validate_required_string_whitespace_only(self):
        """Test that whitespace-only string raises error."""
        with pytest.raises(ValidationError):
            validate_required_string("   ", "test_field")

    def test_validate_required_string_none(self):
        """Test that None raises error."""
        with pytest.raises(ValidationError):
            validate_required_string(None, "test_field")

    def test_validate_required_string_valid(self):
        """Test valid string is accepted."""
        result = validate_required_string("valid_string", "test_field")
        assert result == "valid_string"

    def test_validate_required_string_min_length(self):
        """Test minimum length validation."""
        with pytest.raises(ValidationError):
            validate_required_string("ab", "test_field", min_length=3)

    def test_validate_email_invalid_formats(self):
        """Test various invalid email formats."""
        invalid_emails = [
            "notanemail",
            "@example.com",
            "test@",
            "test@.com",
            "test@domain",
            "test..name@domain.com",
            "",
        ]
        for email in invalid_emails:
            with pytest.raises(ValidationError):
                validate_email(email)

    def test_validate_email_valid_formats(self):
        """Test valid email formats."""
        valid_emails = [
            "user@example.com",
            "test.user@domain.co.uk",
            "user+tag@example.com",
            "123@example.com",
        ]
        for email in valid_emails:
            result = validate_email(email)
            assert "@" in result

    def test_validate_email_case_insensitive(self):
        """Test that email validation is case-insensitive."""
        result = validate_email("TEST@EXAMPLE.COM")
        assert result == "test@example.com"

    def test_validate_password_too_short(self):
        """Test that short passwords are rejected."""
        with pytest.raises(ValidationError):
            validate_password("Short1!")

    def test_validate_password_missing_uppercase(self):
        """Test that password without uppercase is rejected."""
        with pytest.raises(ValidationError):
            validate_password("lowercase1!")

    def test_validate_password_missing_lowercase(self):
        """Test that password without lowercase is rejected."""
        with pytest.raises(ValidationError):
            validate_password("UPPERCASE1!")

    def test_validate_password_missing_digit(self):
        """Test that password without digit is rejected."""
        with pytest.raises(ValidationError):
            validate_password("PasswordNoDigit!")

    def test_validate_password_valid(self):
        """Test that valid password is accepted."""
        result = validate_password("ValidPassword123!")
        assert result == "ValidPassword123!"

    def test_validate_amount_negative(self):
        """Test that negative amounts are rejected."""
        with pytest.raises(ValidationError):
            validate_amount(-10.50)

    def test_validate_amount_invalid_type(self):
        """Test that non-numeric amounts are rejected."""
        with pytest.raises(ValidationError):
            validate_amount("not_a_number")

    def test_validate_amount_valid(self):
        """Test that valid amounts are accepted."""
        result = validate_amount(10.50)
        assert result == 10.50
        assert isinstance(result, float)

    def test_validate_amount_rounding(self):
        """Test that amounts are rounded to 2 decimals."""
        result = validate_amount(10.5555)
        assert result == 10.56

    def test_validate_percentage_below_zero(self):
        """Test that percentage below 0 is rejected."""
        with pytest.raises(ValidationError):
            validate_percentage(-1)

    def test_validate_percentage_above_100(self):
        """Test that percentage above 100 is rejected."""
        with pytest.raises(ValidationError):
            validate_percentage(101)

    def test_validate_percentage_valid_boundaries(self):
        """Test valid percentage values at boundaries."""
        assert validate_percentage(0) == 0
        assert validate_percentage(100) == 100
        assert validate_percentage(50.5) == 50.5

    def test_validate_confidence_score_below_zero(self):
        """Test that confidence below 0 is rejected."""
        with pytest.raises(ValidationError):
            validate_confidence_score(-0.1)

    def test_validate_confidence_score_above_one(self):
        """Test that confidence above 1 is rejected."""
        with pytest.raises(ValidationError):
            validate_confidence_score(1.1)

    def test_validate_confidence_score_valid_boundaries(self):
        """Test valid confidence values."""
        assert validate_confidence_score(0) == 0
        assert validate_confidence_score(1) == 1
        assert validate_confidence_score(0.5) == 0.5


class TestCacheEdgeCases:
    """Test cache behavior for edge cases."""

    @pytest.fixture
    def cache(self):
        """Create a fresh cache for each test."""
        from src.core.cache import SimpleCache

        return SimpleCache()

    def test_cache_expiration(self, cache):
        """Test that expired entries are removed."""
        cache.set("key", "value", ttl_seconds=0)
        # Wait for expiration
        import time

        time.sleep(0.1)
        result = cache.get("key")
        assert result is None

    def test_cache_large_values(self, cache):
        """Test caching large values."""
        large_value = "x" * 10000
        cache.set("large_key", large_value)
        result = cache.get("large_key")
        assert result == large_value

    def test_cache_none_values(self, cache):
        """Test that None values are not cached."""
        cache.set("null_key", None)
        result = cache.get("null_key")
        # None is a valid value, but typically not cached
        assert result is None

    def test_cache_stats(self, cache):
        """Test cache statistics tracking."""
        cache.set("key1", "value1")
        cache.get("key1")  # Hit
        cache.get("key2")  # Miss

        stats = cache.get_stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["hit_rate"] == 50.0


class TestDateHandling:
    """Test date-related edge cases."""

    def test_date_parsing_leap_year(self):
        """Test handling of leap year dates."""
        from src.utils.validators import validate_date_string

        result = validate_date_string("2024-02-29")
        assert result == "2024-02-29"

    def test_date_parsing_invalid_leap_year(self):
        """Test rejection of invalid leap year dates."""
        from src.utils.validators import validate_date_string

        with pytest.raises(ValidationError):
            validate_date_string("2023-02-29")

    def test_date_parsing_format_strict(self):
        """Test that date format must be strict YYYY-MM-DD."""
        from src.utils.validators import validate_date_string

        invalid_formats = [
            "2024/02/29",
            "02-29-2024",
            "2024-2-29",
            "2024-02-9",
            "20240229",
        ]
        for date_str in invalid_formats:
            with pytest.raises(ValidationError):
                validate_date_string(date_str)


class TestConcurrencyEdgeCases:
    """Test edge cases in concurrent scenarios."""

    def test_concurrent_cache_access(self):
        """Test cache behavior under concurrent access."""
        import asyncio
        from src.core.cache import SimpleCache

        cache = SimpleCache()

        async def cache_operation(key, value):
            cache.set(key, value)
            return cache.get(key)

        async def run_test():
            tasks = [cache_operation(f"key_{i}", f"value_{i}") for i in range(100)]
            results = await asyncio.gather(*tasks)
            assert len(results) == 100

        # Run async test with asyncio.run()
        asyncio.run(run_test())

    def test_concurrent_validation(self):
        """Test validation functions under concurrent access."""
        import asyncio

        async def validate_operation(email):
            from src.utils.validators import validate_email

            return validate_email(email)

        async def run_test():
            valid_email = "test@example.com"
            tasks = [validate_operation(valid_email) for _ in range(10)]
            results = await asyncio.gather(*tasks)
            assert len(results) == 10
            assert all(results)

        # Run async test with asyncio.run()
        asyncio.run(run_test())


class TestBoundaryConditions:
    """Test boundary conditions and limits."""

    def test_very_long_string_input(self):
        """Test handling of very long string inputs."""
        long_string = "a" * 100000
        result = validate_required_string(long_string, "field")
        assert len(result) == 100000

    def test_special_characters_in_string(self):
        """Test handling of special characters."""
        special_string = "!@#$%^&*()_+-=[]{}|;:',.<>?/~`"
        result = validate_required_string(special_string, "field")
        assert result == special_string

    def test_unicode_characters(self):
        """Test handling of unicode characters."""
        unicode_string = "مرحبا بك 你好 🎉🎊"
        result = validate_required_string(unicode_string, "field")
        assert result == unicode_string

    def test_sql_injection_attempt_in_string(self):
        """Test that SQL injection strings are safely handled."""
        sql_injection = "'; DROP TABLE users; --"
        result = validate_required_string(sql_injection, "field")
        # Validator should just clean and return the string
        assert result == sql_injection


class TestErrorMessages:
    """Test that error messages are helpful and don't leak info."""

    def test_validation_error_messages(self):
        """Test that validation errors provide helpful messages."""
        with pytest.raises(ValidationError) as exc_info:
            validate_amount("invalid")

        assert "must be a valid number" in str(exc_info.value)

    def test_error_code_assignment(self):
        """Test that errors have proper error codes."""
        with pytest.raises(ValidationError) as exc_info:
            validate_email("invalid.email")

        assert exc_info.value.error_code == "VALIDATION_ERROR"
        assert exc_info.value.status_code == 422
