"""
Pytest configuration and shared fixtures
"""

import pytest
import os
from unittest.mock import MagicMock, create_autospec
from sqlalchemy.orm import Session


@pytest.fixture(autouse=True)
def set_jwt_secret():
    """Set JWT_SECRET environment variable for tests"""
    os.environ["JWT_SECRET"] = "test-secret-key-for-testing-only"
    yield
    if "JWT_SECRET" in os.environ:
        del os.environ["JWT_SECRET"]


@pytest.fixture
def mock_db_session():
    """Provide a mock database session for testing"""
    mock_session = MagicMock(spec=Session)
    return mock_session
