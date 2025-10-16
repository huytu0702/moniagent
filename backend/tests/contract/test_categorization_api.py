"""
Contract test for expense categorization endpoint
"""

import pytest
import os
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from src.api.main import app
from src.core.security import create_access_token


@pytest.fixture(autouse=True)
def set_jwt_secret():
    """Set JWT_SECRET environment variable for tests"""
    os.environ["JWT_SECRET"] = "test-secret-key-for-testing-only"
    yield
    if "JWT_SECRET" in os.environ:
        del os.environ["JWT_SECRET"]


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def auth_headers():
    """Create a valid JWT token for testing"""
    token = create_access_token(subject="test-user-id")
    return {"Authorization": f"Bearer {token}"}


def test_create_category_endpoint_structure(client, auth_headers):
    """Test the structure of the create category endpoint"""

    with patch('src.api.v1.category_router.CategoryService') as mock_service_class:
        mock_instance = mock_service_class.return_value
        mock_instance.create_category.return_value = {
            "id": "category-1",
            "user_id": "test-user-id",
            "name": "Eating Out",
            "description": "Restaurant and food purchases",
            "icon": "🍽️",
            "color": "#FF5733",
            "is_system_category": False,
            "display_order": 0,
            "created_at": "2023-10-15T10:00:00",
            "updated_at": "2023-10-15T10:00:00",
        }

        response = client.post(
            "/api/v1/categories",
            json={
                "name": "Eating Out",
                "description": "Restaurant and food purchases",
                "icon": "🍽️",
                "color": "#FF5733",
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        response_data = response.json()

        # Verify response structure
        assert "id" in response_data
        assert "name" in response_data
        assert "user_id" in response_data
        assert "description" in response_data
        assert "icon" in response_data
        assert "color" in response_data
        assert "is_system_category" in response_data

        # Verify data types
        assert isinstance(response_data["id"], str)
        assert isinstance(response_data["name"], str)
        assert isinstance(response_data["is_system_category"], bool)


def test_get_categories_endpoint_structure(client, auth_headers):
    """Test the structure of the get categories endpoint"""

    with patch('src.api.v1.category_router.CategoryService') as mock_service_class:
        mock_instance = mock_service_class.return_value
        mock_instance.get_user_categories.return_value = [
            {
                "id": "category-1",
                "user_id": "test-user-id",
                "name": "Eating Out",
                "description": "Restaurant purchases",
                "icon": "🍽️",
                "color": "#FF5733",
                "is_system_category": False,
                "display_order": 0,
                "created_at": "2023-10-15T10:00:00",
                "updated_at": "2023-10-15T10:00:00",
            },
            {
                "id": "category-2",
                "user_id": "test-user-id",
                "name": "Transportation",
                "description": "Travel expenses",
                "icon": "🚗",
                "color": "#3366FF",
                "is_system_category": False,
                "display_order": 1,
                "created_at": "2023-10-15T11:00:00",
                "updated_at": "2023-10-15T11:00:00",
            },
        ]

        response = client.get(
            "/api/v1/categories",
            headers=auth_headers,
        )

        assert response.status_code == 200
        response_data = response.json()

        # Verify response structure
        assert "categories" in response_data
        assert isinstance(response_data["categories"], list)
        assert len(response_data["categories"]) == 2

        # Check first category structure
        category = response_data["categories"][0]
        assert "id" in category
        assert "name" in category
        assert "user_id" in category


def test_categorize_expense_endpoint_structure(client, auth_headers):
    """Test the structure of the categorize expense endpoint"""

    with patch(
        'src.api.v1.category_router.CategorizationService'
    ) as mock_service_class:
        mock_instance = mock_service_class.return_value
        mock_instance.suggest_category.return_value = {
            "suggested_category_id": "category-1",
            "suggested_category_name": "Eating Out",
            "confidence_score": 0.95,
            "reason": "Matched with 'Restaurant' rule",
        }

        response = client.post(
            "/api/v1/categories/suggest",
            json={"expense_id": "expense-1"},
            headers=auth_headers,
        )

        assert response.status_code == 200
        response_data = response.json()

        # Verify response structure
        assert "suggested_category_id" in response_data
        assert "suggested_category_name" in response_data
        assert "confidence_score" in response_data

        # Verify data types
        assert isinstance(response_data["suggested_category_id"], str)
        assert isinstance(response_data["confidence_score"], (float, int))


def test_create_categorization_rule_endpoint_structure(client, auth_headers):
    """Test the structure of the create categorization rule endpoint"""

    with patch('src.api.v1.category_router.CategoryService') as mock_service_class:
        mock_instance = mock_service_class.return_value
        mock_instance.create_categorization_rule.return_value = {
            "id": "rule-1",
            "user_id": "test-user-id",
            "category_id": "category-1",
            "store_name_pattern": "Restaurant",
            "rule_type": "keyword",
            "confidence_threshold": 0.8,
            "is_active": True,
            "created_at": "2023-10-15T10:00:00",
            "updated_at": "2023-10-15T10:00:00",
        }

        response = client.post(
            "/api/v1/categories/rules",
            json={
                "category_id": "category-1",
                "store_name_pattern": "Restaurant",
                "rule_type": "keyword",
                "confidence_threshold": 0.8,
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        response_data = response.json()

        # Verify response structure
        assert "id" in response_data
        assert "category_id" in response_data
        assert "store_name_pattern" in response_data
        assert "rule_type" in response_data
        assert "confidence_threshold" in response_data
        assert "is_active" in response_data


def test_missing_required_fields_in_category_creation(client, auth_headers):
    """Test that missing required fields in category creation are rejected"""

    response = client.post(
        "/api/v1/categories",
        json={"description": "No name provided"},
        headers=auth_headers,
    )

    assert response.status_code == 422  # Unprocessable entity


def test_confirm_categorization_endpoint_structure(client, auth_headers):
    """Test the structure of the confirm categorization endpoint"""

    with patch(
        'src.api.v1.category_router.CategorizationService'
    ) as mock_service_class:
        mock_instance = mock_service_class.return_value
        mock_instance.confirm_categorization.return_value = {
            "expense_id": "expense-1",
            "category_id": "category-1",
            "category_name": "Eating Out",
            "confidence_score": 0.95,
            "is_user_confirmed": True,
        }

        response = client.post(
            "/api/v1/categories/confirm",
            json={"expense_id": "expense-1", "category_id": "category-1"},
            headers=auth_headers,
        )

        assert response.status_code == 200
        response_data = response.json()

        # Verify response structure
        assert "expense_id" in response_data
        assert "category_id" in response_data
        assert "category_name" in response_data
        assert "is_user_confirmed" in response_data
        assert response_data["is_user_confirmed"] is True
