"""
Contract test for budget management endpoint
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


def test_create_budget_endpoint_structure(client, auth_headers):
    """Test the structure of the create budget endpoint"""

    with patch('src.api.v1.budget_router.BudgetManagementService') as mock_service_class:
        mock_instance = mock_service_class.return_value
        mock_instance.create_budget.return_value = {
            "id": "budget-1",
            "user_id": "test-user-id",
            "category_id": "category-1",
            "category_name": "Eating Out",
            "limit_amount": 500.0,
            "period": "monthly",
            "spent_amount": 250.0,
            "remaining_amount": 250.0,
            "alert_threshold": 0.8,
            "created_at": "2025-10-16T10:00:00",
            "updated_at": "2025-10-16T10:00:00",
        }

        response = client.post(
            "/api/v1/budgets",
            json={
                "category_id": "category-1",
                "limit_amount": 500.0,
                "period": "monthly",
                "alert_threshold": 0.8,
            },
            headers=auth_headers,
        )

        assert response.status_code in [200, 201]
        response_data = response.json()

        # Verify response structure
        assert "id" in response_data
        assert "user_id" in response_data
        assert "category_id" in response_data
        assert "category_name" in response_data
        assert "limit_amount" in response_data
        assert "spent_amount" in response_data
        assert "remaining_amount" in response_data

        # Verify data types
        assert isinstance(response_data["id"], str)
        assert isinstance(response_data["limit_amount"], (int, float))
        assert isinstance(response_data["spent_amount"], (int, float))


def test_get_budgets_endpoint_structure(client, auth_headers):
    """Test the structure of the get budgets endpoint"""

    with patch('src.api.v1.budget_router.BudgetManagementService') as mock_service_class:
        mock_instance = mock_service_class.return_value
        mock_instance.get_user_budgets.return_value = [
            {
                "id": "budget-1",
                "user_id": "test-user-id",
                "category_id": "category-1",
                "category_name": "Eating Out",
                "limit_amount": 500.0,
                "period": "monthly",
                "spent_amount": 250.0,
                "remaining_amount": 250.0,
                "alert_threshold": 0.8,
                "created_at": "2025-10-16T10:00:00",
                "updated_at": "2025-10-16T10:00:00",
            }
        ]

        response = client.get(
            "/api/v1/budgets",
            headers=auth_headers,
        )

        assert response.status_code == 200
        response_data = response.json()

        # Verify response is a list
        assert isinstance(response_data, list)
        if len(response_data) > 0:
            # Verify first item structure
            assert "id" in response_data[0]
            assert "limit_amount" in response_data[0]
            assert "spent_amount" in response_data[0]


def test_get_spending_summary_endpoint_structure(client, auth_headers):
    """Test the structure of the get spending summary endpoint"""

    with patch('src.api.v1.budget_router.ExpenseAggregationService') as mock_service_class:
        mock_instance = mock_service_class.return_value
        mock_instance.get_spending_summary.return_value = {
            "period": "monthly",
            "total_spending": 1500.0,
            "by_category": [
                {
                    "category_id": "category-1",
                    "category_name": "Eating Out",
                    "amount": 500.0,
                    "percentage": 33.3,
                }
            ],
            "by_week": [
                {
                    "week": "2025-W42",
                    "amount": 300.0,
                    "percentage": 20.0,
                }
            ],
        }

        response = client.get(
            "/api/v1/spending/summary",
            headers=auth_headers,
        )

        assert response.status_code == 200
        response_data = response.json()

        # Verify response structure
        assert "period" in response_data
        assert "total_spending" in response_data
        assert "by_category" in response_data or "by_week" in response_data


def test_get_financial_advice_endpoint_structure(client, auth_headers):
    """Test the structure of the get financial advice endpoint"""

    with patch('src.api.v1.ai_agent_router.FinancialAdviceService') as mock_service_class:
        mock_instance = mock_service_class.return_value
        mock_instance.get_financial_advice.return_value = {
            "advice": "You are spending 33% of your budget on dining. Consider reducing to save more.",
            "recommendations": [
                "Cook at home more often",
                "Set a daily limit for dining out",
            ],
            "spending_pattern": "high",
            "period": "monthly",
        }

        response = client.get(
            "/api/v1/financial-advice",
            headers=auth_headers,
        )

        assert response.status_code == 200
        response_data = response.json()

        # Verify response structure
        assert "advice" in response_data
        assert isinstance(response_data["advice"], str)


def test_missing_required_fields_in_budget_creation(client, auth_headers):
    """Test that missing required fields returns error"""

    with patch('src.api.v1.budget_router.BudgetManagementService') as mock_service_class:
        mock_instance = mock_service_class.return_value
        mock_instance.create_budget.side_effect = ValueError(
            "Missing required field: category_id"
        )

        response = client.post(
            "/api/v1/budgets",
            json={
                "limit_amount": 500.0,
                "period": "monthly",
            },
            headers=auth_headers,
        )

        # Should fail validation
        assert response.status_code in [400, 422]
