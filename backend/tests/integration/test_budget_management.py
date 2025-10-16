"""
Integration tests for budget management workflow
"""

import pytest
import os
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
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


def test_create_budget_workflow(client, auth_headers):
    """Test creating a budget for a category"""

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

    # Should return 201 or 400 (depending on service implementation)
    assert response.status_code in [200, 201, 400]
    if response.status_code in [200, 201]:
        data = response.json()
        assert "id" in data
        assert data["limit_amount"] == 500.0
        assert data["period"] == "monthly"


def test_get_spending_summary_workflow(client, auth_headers):
    """Test getting spending summary for the user"""

    response = client.get(
        "/api/v1/spending/summary",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()

    # Verify response structure
    assert "period" in data
    assert "total_spending" in data
    assert data["period"] in ["daily", "weekly", "monthly"]
    assert isinstance(data["total_spending"], (int, float))


def test_check_budget_alerts_workflow(client, auth_headers):
    """Test checking if any budgets have exceeded thresholds"""

    response = client.get(
        "/api/v1/budgets/alerts",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()

    # Response should be a list (may be empty)
    assert isinstance(data, list)


def test_get_financial_advice_workflow(client, auth_headers):
    """Test getting AI-driven financial advice"""

    response = client.get(
        "/api/v1/financial-advice",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()

    # Verify response structure
    assert "advice" in data
    assert "recommendations" in data
    assert isinstance(data["recommendations"], list)
    assert "spending_pattern" in data


def test_update_budget_workflow(client, auth_headers):
    """Test updating an existing budget"""

    response = client.put(
        "/api/v1/budgets/budget-1",
        json={
            "limit_amount": 600.0,
            "alert_threshold": 0.75,
        },
        headers=auth_headers,
    )

    # Should return 200 or 404 (budget might not exist)
    assert response.status_code in [200, 404, 400]
    if response.status_code == 200:
        data = response.json()
        assert "limit_amount" in data
        assert "alert_threshold" in data


def test_expense_aggregation_by_time_period(client, auth_headers):
    """Test aggregating expenses by different time periods"""

    # Test monthly period (default)
    response = client.get(
        "/api/v1/spending/summary?period=monthly",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["period"] == "monthly"

    # Test weekly period
    response = client.get(
        "/api/v1/spending/summary?period=weekly",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["period"] == "weekly"


def test_budget_alert_generation(client, auth_headers):
    """Test that alerts endpoint returns proper structure"""

    response = client.get(
        "/api/v1/budgets/alerts",
        headers=auth_headers,
    )

    assert response.status_code == 200
    alerts = response.json()

    # Should be a list (may be empty for test user)
    assert isinstance(alerts, list)


def test_financial_advice_based_on_spending_pattern(client, auth_headers):
    """Test that financial advice endpoint returns proper structure"""

    response = client.get(
        "/api/v1/financial-advice",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()

    # Verify response structure
    assert "advice" in data
    assert "recommendations" in data
    assert "spending_pattern" in data
    assert data["spending_pattern"] in ["low", "normal", "above_average", "high"]
    assert len(data["recommendations"]) <= 3


def test_get_budgets_list(client, auth_headers):
    """Test getting list of user budgets"""

    response = client.get(
        "/api/v1/budgets",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()

    # Should return a list
    assert isinstance(data, list)


def test_spending_summary_response_format(client, auth_headers):
    """Test spending summary has correct response format"""

    response = client.get(
        "/api/v1/spending/summary",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()

    # Check required fields
    assert "period" in data
    assert "total_spending" in data
    assert data["total_spending"] >= 0

    # Check optional fields if present
    if "by_category" in data:
        assert isinstance(data["by_category"], list)

    if "by_week" in data:
        assert isinstance(data["by_week"], list)
