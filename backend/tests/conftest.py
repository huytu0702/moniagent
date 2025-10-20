"""
Pytest configuration and shared fixtures for comprehensive testing
"""

import pytest
import os
from typing import Generator, AsyncGenerator
from unittest.mock import MagicMock, create_autospec, AsyncMock
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
import tempfile
import json
from datetime import datetime, timedelta


# ===== Environment Setup =====
@pytest.fixture(autouse=True, scope="function")
def set_jwt_secret():
    """Set JWT_SECRET environment variable for tests"""
    os.environ["JWT_SECRET"] = "test-secret-key-for-testing-only"
    os.environ["ENV"] = "testing"
    os.environ["LOG_LEVEL"] = "DEBUG"
    yield
    if "JWT_SECRET" in os.environ:
        del os.environ["JWT_SECRET"]


# ===== Database Fixtures =====
@pytest.fixture
def test_db_url():
    """Return in-memory SQLite database URL for testing"""
    return "sqlite:///:memory:"


@pytest.fixture
def test_db_session(test_db_url) -> Generator:
    """Create a test database session"""
    # Import all models to register them with SQLAlchemy Base before creating tables
    from src.core.database import Base
    import src.models  # noqa: F401

    engine = create_engine(
        test_db_url,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)

    SessionLocal = __import__('sqlalchemy.orm', fromlist=['sessionmaker']).sessionmaker(
        autocommit=False, autoflush=False, bind=engine
    )
    db = SessionLocal()

    yield db

    db.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def mock_db_session():
    """Provide a mock database session for unit tests"""
    mock_session = MagicMock(spec=Session)
    return mock_session


# ===== Authentication Fixtures =====
@pytest.fixture
def auth_token():
    """Generate a valid test JWT token"""
    from src.core.security import create_access_token

    token = create_access_token(subject="test-user-id", extra_claims={"role": "user"})
    return token


@pytest.fixture
def admin_token():
    """Generate an admin JWT token for testing"""
    from src.core.security import create_access_token

    token = create_access_token(subject="test-admin-id", extra_claims={"role": "admin"})
    return token


@pytest.fixture
def auth_headers(auth_token):
    """Generate authorization headers with valid token"""
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture
def admin_headers(admin_token):
    """Generate admin authorization headers"""
    return {"Authorization": f"Bearer {admin_token}"}


# ===== FastAPI TestClient Fixtures =====
@pytest.fixture
def api_client(test_db_session) -> TestClient:
    """Create FastAPI test client with database dependency override"""
    from src.api.main import app
    from src.core.database import get_db

    def override_get_db():
        try:
            yield test_db_session
        finally:
            # Don't close the session here since it's managed by the test_db_session fixture
            pass

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)

    # Clean up the override after the test
    yield client
    app.dependency_overrides.clear()


# ===== Mock Services =====
@pytest.fixture
def mock_supabase_client():
    """Mock Supabase client"""
    mock = MagicMock()
    mock.table = MagicMock(return_value=MagicMock())
    return mock


@pytest.fixture
def mock_google_ai_client():
    """Mock Google AI SDK client"""
    mock = AsyncMock()
    mock.generate_content = AsyncMock(return_value=MagicMock(text="Mock AI response"))
    return mock


@pytest.fixture
def mock_storage():
    """Mock file storage for uploads"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    # Cleanup could be added here


# ===== Test Data Factories =====
@pytest.fixture
def valid_expense_data():
    """Generate valid expense data for testing"""
    return {
        "price": 25.50,
        "location": "Coffee Shop",
        "date": datetime.now().date().isoformat(),
        "category_id": "test-category-id",
        "description": "Morning coffee",
    }


@pytest.fixture
def valid_chat_message():
    """Generate valid chat message data"""
    return {
        "session_id": "test-session-id",
        "content": "I spent $25 on coffee today",
        "message_type": "text",
    }


@pytest.fixture
def valid_image_upload(tmp_path):
    """Generate mock image file for testing"""
    from PIL import Image

    img = Image.new('RGB', (100, 100), color='red')
    img_path = tmp_path / "test_invoice.png"
    img.save(img_path)
    return str(img_path)


@pytest.fixture
def valid_user_data():
    """Generate valid user registration data"""
    return {
        "email": "test@example.com",
        "password": "SecurePass123!",
        "first_name": "Test",
        "last_name": "User",
    }


@pytest.fixture
def valid_budget_data():
    """Generate valid budget data"""
    return {
        "category_id": "test-category-id",
        "monthly_limit": 500.00,
        "currency": "USD",
    }


# ===== Mock Response Builders =====
@pytest.fixture
def mock_ocr_response():
    """Generate mock OCR response data"""
    return {
        "price": "25.50",
        "location": "Coffee Shop",
        "date": datetime.now().date().isoformat(),
        "confidence": 0.95,
        "raw_text": "Mock invoice text",
    }


@pytest.fixture
def mock_ai_extraction_response():
    """Generate mock AI extraction response"""
    return {
        "expense": {
            "price": 25.50,
            "location": "Coffee Shop",
            "date": datetime.now().date().isoformat(),
        },
        "confidence": 0.92,
        "needs_confirmation": True,
    }


# ===== Mocking Utilities =====
@pytest.fixture
def mock_env_variables(monkeypatch):
    """Fixture to set environment variables for tests"""

    def _set_env(**kwargs):
        for key, value in kwargs.items():
            monkeypatch.setenv(key, str(value))

    return _set_env


@pytest.fixture
def mock_time(monkeypatch):
    """Fixture to mock time/datetime for consistent testing"""
    from unittest.mock import MagicMock

    def _mock_now():
        return datetime(2025, 1, 15, 12, 0, 0)

    return _mock_now


# ===== Helper Functions =====
class TestHelpers:
    """Helper methods for common testing tasks"""

    @staticmethod
    def create_jwt_token(user_id: str, expires_in_hours: int = 24) -> str:
        """Create a JWT token for testing"""
        from src.core.security import create_access_token
        from datetime import timedelta

        expires_delta = timedelta(hours=expires_in_hours)
        return create_access_token(subject=user_id, expires_delta=expires_delta)

    @staticmethod
    def validate_json_response(response, expected_keys: list = None) -> bool:
        """Validate JSON response structure"""
        try:
            data = response.json()
            if expected_keys:
                return all(key in data for key in expected_keys)
            return True
        except Exception:
            return False

    @staticmethod
    def create_mock_file(filename: str, content: bytes) -> tuple:
        """Create mock file for testing"""
        import io

        file_obj = io.BytesIO(content)
        file_obj.name = filename
        return file_obj


@pytest.fixture
def test_helpers():
    """Provide test helper methods"""
    return TestHelpers()


# ===== Test Model Fixtures =====
@pytest.fixture
def test_user(test_db_session):
    """Create a test user"""
    from src.models.user import User

    user = User(
        id="test-user-id",
        email="test@example.com",
        hashed_password="hashed_password_here",
        first_name="Test",
        last_name="User",
    )
    test_db_session.add(user)
    test_db_session.commit()
    test_db_session.refresh(user)
    return user


@pytest.fixture
def test_category(test_db_session):
    """Create a test expense category"""
    from src.models.category import Category

    category = Category(
        id="test-category-id",
        user_id="test-user-id",
        name="Food & Dining",
        description="Food and dining expenses",
    )
    test_db_session.add(category)
    test_db_session.commit()
    test_db_session.refresh(category)
    return category


@pytest.fixture
def test_expense(test_db_session, test_user, test_category):
    """Create a test expense"""
    from src.models.expense import Expense
    from datetime import datetime

    expense = Expense(
        id="test-expense-id",
        user_id=test_user.id,
        category_id=test_category.id,
        merchant_name="Test Coffee Shop",
        amount=25.50,
        date=datetime.now(),
        description="Test expense",
        confirmed_by_user=False,
        source_type="text",
    )
    test_db_session.add(expense)
    test_db_session.commit()
    test_db_session.refresh(expense)
    return expense


# ===== Cleanup and Teardown =====
@pytest.fixture(autouse=True)
def cleanup_uploads():
    """Clean up uploaded test files after each test"""
    yield
    # Cleanup logic can be added here
