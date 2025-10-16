"""
Contract tests for Expense API endpoints
Tests the API contract and response formats for expense management and corrections
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime


class TestGetExpensesEndpoint:
    """Contract tests for GET /expenses endpoint"""

    def test_get_expenses_success(self, api_client: TestClient, auth_headers: dict):
        """Test getting user expenses successfully"""
        response = api_client.get(
            "/api/v1/expenses",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "expenses" in data
        assert isinstance(data["expenses"], list)

    def test_get_expenses_with_filters(
        self, api_client: TestClient, auth_headers: dict
    ):
        """Test getting expenses with category filter"""
        response = api_client.get(
            "/api/v1/expenses?category_id=cat-123",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "expenses" in data

    def test_get_expenses_unauthenticated(self, api_client: TestClient):
        """Test getting expenses without authentication"""
        response = api_client.get("/api/v1/expenses")
        assert response.status_code in [401, 403]


class TestGetExpenseByIdEndpoint:
    """Contract tests for GET /expenses/{expenseId} endpoint"""

    def test_get_expense_by_id_success(
        self, api_client: TestClient, auth_headers: dict, test_expense
    ):
        """Test getting a specific expense by ID"""
        response = api_client.get(
            f"/api/v1/expenses/{test_expense.id}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "id" in data
        assert "amount" in data
        assert "merchant_name" in data
        assert "date" in data
        assert "category_id" in data
        assert "confirmed_by_user" in data

        # Verify data matches
        assert data["id"] == test_expense.id
        assert data["amount"] == test_expense.amount

    def test_get_expense_nonexistent(self, api_client: TestClient, auth_headers: dict):
        """Test getting a non-existent expense"""
        response = api_client.get(
            "/api/v1/expenses/nonexistent-expense-id",
            headers=auth_headers,
        )

        assert response.status_code == 404

    def test_get_expense_unauthenticated(self, api_client: TestClient):
        """Test getting an expense without authentication"""
        response = api_client.get("/api/v1/expenses/some-expense-id")
        assert response.status_code in [401, 403]


class TestUpdateExpenseEndpoint:
    """Contract tests for PUT /expenses/{expenseId} endpoint - User Story 2"""

    def test_update_expense_success(
        self, api_client: TestClient, auth_headers: dict, test_expense
    ):
        """Test updating an expense with corrections"""
        update_data = {
            "merchant_name": "Corrected Merchant",
            "amount": 35.50,
            "date": "2025-10-15",
        }

        response = api_client.put(
            f"/api/v1/expenses/{test_expense.id}",
            json=update_data,
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "id" in data
        assert "amount" in data
        assert "merchant_name" in data
        assert "date" in data
        assert "message" in data

        # Verify updated values
        assert data["amount"] == 35.50
        assert data["merchant_name"] == "Corrected Merchant"
        assert "updated" in data["message"].lower()

    def test_update_expense_partial(
        self, api_client: TestClient, auth_headers: dict, test_expense
    ):
        """Test partially updating an expense (only amount)"""
        update_data = {"amount": 42.00}

        response = api_client.put(
            f"/api/v1/expenses/{test_expense.id}",
            json=update_data,
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        assert data["amount"] == 42.00
        # Other fields should remain unchanged
        assert data["merchant_name"] == test_expense.merchant_name

    def test_update_expense_with_invalid_amount(
        self, api_client: TestClient, auth_headers: dict, test_expense
    ):
        """Test updating expense with invalid amount"""
        update_data = {"amount": -10.00}  # Negative amount

        response = api_client.put(
            f"/api/v1/expenses/{test_expense.id}",
            json=update_data,
            headers=auth_headers,
        )

        assert response.status_code == 422  # Validation error

    def test_update_expense_with_invalid_date(
        self, api_client: TestClient, auth_headers: dict, test_expense
    ):
        """Test updating expense with invalid date format"""
        update_data = {"date": "invalid-date-format"}

        response = api_client.put(
            f"/api/v1/expenses/{test_expense.id}",
            json=update_data,
            headers=auth_headers,
        )

        assert response.status_code in [400, 422]

    def test_update_nonexistent_expense(
        self, api_client: TestClient, auth_headers: dict
    ):
        """Test updating a non-existent expense"""
        update_data = {"amount": 50.00}

        response = api_client.put(
            "/api/v1/expenses/nonexistent-expense-id",
            json=update_data,
            headers=auth_headers,
        )

        assert response.status_code == 404

    def test_update_expense_unauthenticated(self, api_client: TestClient):
        """Test updating expense without authentication"""
        update_data = {"amount": 50.00}

        response = api_client.put(
            "/api/v1/expenses/some-expense-id",
            json=update_data,
        )

        assert response.status_code in [401, 403]

    def test_update_expense_stores_correction_history(
        self, api_client: TestClient, auth_headers: dict, test_expense
    ):
        """Test that updating expense stores correction for learning"""
        original_amount = test_expense.amount
        update_data = {
            "merchant_name": "New Merchant Name",
            "amount": 99.99,
        }

        response = api_client.put(
            f"/api/v1/expenses/{test_expense.id}",
            json=update_data,
            headers=auth_headers,
        )

        assert response.status_code == 200

        # The correction should be stored (we'll verify this in integration tests)
        # For contract test, we just verify the API contract is correct
        data = response.json()
        assert data["merchant_name"] == "New Merchant Name"
        assert data["amount"] == 99.99


class TestDeleteExpenseEndpoint:
    """Contract tests for DELETE /expenses/{expenseId} endpoint"""

    def test_delete_expense_success(
        self, api_client: TestClient, auth_headers: dict, test_expense
    ):
        """Test deleting an expense"""
        response = api_client.delete(
            f"/api/v1/expenses/{test_expense.id}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "message" in data
        assert "deleted" in data["message"].lower()

    def test_delete_nonexistent_expense(
        self, api_client: TestClient, auth_headers: dict
    ):
        """Test deleting a non-existent expense"""
        response = api_client.delete(
            "/api/v1/expenses/nonexistent-expense-id",
            headers=auth_headers,
        )

        assert response.status_code == 404

    def test_delete_expense_unauthenticated(self, api_client: TestClient):
        """Test deleting expense without authentication"""
        response = api_client.delete("/api/v1/expenses/some-expense-id")
        assert response.status_code in [401, 403]
