"""
Unit tests for budget management and expense aggregation services
"""

import pytest
from unittest.mock import patch, MagicMock
from src.services.budget_management_service import (
    BudgetManagementService,
    BudgetManagementServiceError,
)
from src.services.expense_aggregation_service import (
    ExpenseAggregationService,
    ExpenseAggregationServiceError,
)
from src.services.financial_advice_service import (
    FinancialAdviceService,
    FinancialAdviceServiceError,
)


@pytest.fixture
def budget_service():
    return BudgetManagementService()


@pytest.fixture
def aggregation_service():
    return ExpenseAggregationService()


@pytest.fixture
def advice_service():
    return FinancialAdviceService()


class TestBudgetManagementService:
    """Tests for BudgetManagementService"""

    def test_create_budget_success(self, budget_service):
        """Test successful budget creation"""
        result = budget_service.create_budget(
            user_id="user-123",
            category_id="cat-1",
            limit_amount=500.0,
            period="monthly",
            alert_threshold=0.8,
        )

        assert result is not None
        assert result["id"] is not None
        assert result["user_id"] == "user-123"
        assert result["category_id"] == "cat-1"
        assert result["limit_amount"] == 500.0
        assert result["period"] == "monthly"
        assert result["alert_threshold"] == 0.8

    def test_create_budget_missing_category(self, budget_service):
        """Test budget creation with missing category"""
        with pytest.raises(BudgetManagementServiceError):
            budget_service.create_budget(
                user_id="user-123",
                category_id="",
                limit_amount=500.0,
            )

    def test_create_budget_invalid_amount(self, budget_service):
        """Test budget creation with invalid amount"""
        with pytest.raises(BudgetManagementServiceError):
            budget_service.create_budget(
                user_id="user-123",
                category_id="cat-1",
                limit_amount=-100.0,
            )

    def test_create_budget_invalid_threshold(self, budget_service):
        """Test budget creation with invalid threshold"""
        with pytest.raises(BudgetManagementServiceError):
            budget_service.create_budget(
                user_id="user-123",
                category_id="cat-1",
                limit_amount=500.0,
                alert_threshold=1.5,
            )

    def test_get_user_budgets(self, budget_service):
        """Test fetching user budgets"""
        result = budget_service.get_user_budgets(user_id="user-123")

        assert isinstance(result, list)

    def test_update_budget_success(self, budget_service):
        """Test successful budget update"""
        result = budget_service.update_budget(
            user_id="user-123",
            budget_id="budget-1",
            limit_amount=600.0,
            alert_threshold=0.75,
        )

        assert result is not None
        assert result["limit_amount"] == 600.0
        assert result["alert_threshold"] == 0.75

    def test_update_budget_invalid_amount(self, budget_service):
        """Test budget update with invalid amount"""
        with pytest.raises(BudgetManagementServiceError):
            budget_service.update_budget(
                user_id="user-123",
                budget_id="budget-1",
                limit_amount=-100.0,
            )

    def test_check_budget_alerts(self, budget_service):
        """Test checking budget alerts"""
        result = budget_service.check_budget_alerts(user_id="user-123")

        assert isinstance(result, list)

    def test_delete_budget(self, budget_service):
        """Test deleting a budget"""
        result = budget_service.delete_budget(
            user_id="user-123",
            budget_id="budget-1",
        )

        assert result is True


class TestExpenseAggregationService:
    """Tests for ExpenseAggregationService"""

    def test_get_spending_summary_monthly(self, aggregation_service):
        """Test spending summary for monthly period"""
        result = aggregation_service.get_spending_summary(
            user_id="user-123",
            period="monthly",
        )

        assert result is not None
        assert result["period"] == "monthly"
        assert "total_spending" in result
        assert "by_category" in result
        assert "by_week" in result

    def test_get_spending_summary_weekly(self, aggregation_service):
        """Test spending summary for weekly period"""
        result = aggregation_service.get_spending_summary(
            user_id="user-123",
            period="weekly",
        )

        assert result is not None
        assert result["period"] == "weekly"
        assert result["total_spending"] > 0

    def test_get_spending_summary_daily(self, aggregation_service):
        """Test spending summary for daily period"""
        result = aggregation_service.get_spending_summary(
            user_id="user-123",
            period="daily",
        )

        assert result is not None
        assert result["period"] == "daily"

    def test_get_spending_by_category(self, aggregation_service):
        """Test spending breakdown by category"""
        result = aggregation_service.get_spending_by_category(
            user_id="user-123",
            period="monthly",
        )

        assert isinstance(result, list)

    def test_get_spending_by_week(self, aggregation_service):
        """Test spending breakdown by week"""
        result = aggregation_service.get_spending_by_week(
            user_id="user-123",
            num_weeks=4,
        )

        assert isinstance(result, list)


class TestFinancialAdviceService:
    """Tests for FinancialAdviceService"""

    def test_get_financial_advice_monthly(self, advice_service):
        """Test financial advice generation for monthly period"""
        result = advice_service.get_financial_advice(
            user_id="user-123",
            period="monthly",
        )

        assert result is not None
        assert "advice" in result
        assert "recommendations" in result
        assert "spending_pattern" in result
        assert isinstance(result["recommendations"], list)

    def test_get_financial_advice_weekly(self, advice_service):
        """Test financial advice generation for weekly period"""
        result = advice_service.get_financial_advice(
            user_id="user-123",
            period="weekly",
        )

        assert result is not None
        assert result["period"] == "weekly"

    def test_analyze_spending(self, advice_service):
        """Test spending analysis"""
        result = advice_service._analyze_spending(
            user_id="user-123",
            period="monthly",
            db_session=None,
        )

        assert result is not None
        assert "total_spending" in result
        assert "by_category" in result
        assert "average_daily" in result

    def test_determine_spending_pattern_low(self, advice_service):
        """Test low spending pattern detection"""
        analysis = {
            "total_spending": 100.0,
            "average_daily": 20.0,
        }
        pattern = advice_service._determine_spending_pattern(analysis)

        assert pattern == "low"

    def test_determine_spending_pattern_high(self, advice_service):
        """Test high spending pattern detection"""
        analysis = {
            "total_spending": 2000.0,
            "average_daily": 100.0,
        }
        pattern = advice_service._determine_spending_pattern(analysis)

        assert pattern == "high"

    def test_extract_recommendations(self, advice_service):
        """Test recommendation extraction from advice"""
        advice_text = "1. Cook at home more often\n2. Reduce dining out\n3. Use budget tracking apps"
        recommendations = advice_service._extract_recommendations(advice_text)

        assert isinstance(recommendations, list)
        assert len(recommendations) <= 3
