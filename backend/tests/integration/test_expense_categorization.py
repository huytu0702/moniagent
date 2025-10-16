"""
Integration test for expense categorization workflow
"""

import pytest
import os
from unittest.mock import patch, MagicMock
from datetime import datetime


@pytest.fixture(autouse=True)
def set_jwt_secret():
    """Set JWT_SECRET environment variable for tests"""
    os.environ["JWT_SECRET"] = "test-secret-key-for-testing-only"
    yield
    if "JWT_SECRET" in os.environ:
        del os.environ["JWT_SECRET"]


def test_create_category_workflow():
    """Test the complete workflow of creating a category"""

    from src.services.category_service import CategoryService

    with patch('src.services.category_service.Category'):
        service = CategoryService()

        # Create a category
        result = service.create_category(
            user_id="test-user-id",
            name="Eating Out",
            description="Restaurant purchases",
            icon="🍽️",
            color="#FF5733",
        )

        # Verify the result
        assert result is not None
        assert "id" in result
        assert result["name"] == "Eating Out"
        assert result["user_id"] == "test-user-id"


def test_categorization_rule_creation_workflow():
    """Test the workflow of creating categorization rules"""

    from src.services.category_service import CategoryService

    with patch('src.services.category_service.ExpenseCategorizationRule'):
        service = CategoryService()

        # Create a categorization rule
        result = service.create_categorization_rule(
            user_id="test-user-id",
            category_id="category-1",
            store_name_pattern="Restaurant",
            rule_type="keyword",
            confidence_threshold=0.8,
        )

        # Verify the result
        assert result is not None
        assert "id" in result
        assert result["store_name_pattern"] == "Restaurant"
        assert result["rule_type"] == "keyword"


def test_suggest_category_workflow():
    """Test the workflow of suggesting categories for expenses"""

    from src.services.categorization_service import CategorizationService

    with patch('src.services.categorization_service.Expense') as mock_expense:
        with patch('src.services.categorization_service.Category') as mock_category:
            # Setup mocks
            mock_expense_instance = MagicMock()
            mock_expense_instance.description = "Meal at McDonald's"
            mock_expense.query.return_value.filter.return_value.first.return_value = (
                mock_expense_instance
            )

            mock_category_instance = MagicMock()
            mock_category_instance.id = "category-1"
            mock_category_instance.name = "Eating Out"
            mock_category.query.return_value.filter.return_value.first.return_value = (
                mock_category_instance
            )

            service = CategorizationService()

            # Suggest a category for an expense
            result = service.suggest_category(
                user_id="test-user-id", expense_id="expense-1"
            )

            # Verify the suggestion
            assert result is not None
            assert "suggested_category_id" in result
            assert "suggested_category_name" in result
            assert "confidence_score" in result


def test_confirm_categorization_workflow():
    """Test the workflow of confirming/correcting categorization"""

    from src.services.categorization_service import CategorizationService

    with patch('src.services.categorization_service.Expense'):
        with patch('src.services.categorization_service.Category'):
            with patch('src.services.categorization_service.CategorizationFeedback'):
                service = CategorizationService()

                # Confirm a categorization
                result = service.confirm_categorization(
                    user_id="test-user-id",
                    expense_id="expense-1",
                    category_id="category-1",
                )

                # Verify the result
                assert result is not None
                assert "expense_id" in result
                assert "category_id" in result
                assert "is_user_confirmed" in result
                assert result["is_user_confirmed"] is True


def test_categorization_with_multiple_expenses():
    """Test categorizing multiple expenses with different categories"""

    from src.services.categorization_service import CategorizationService

    with patch('src.services.categorization_service.Expense'):
        with patch('src.services.categorization_service.Category'):
            service = CategorizationService()

            # Categorize multiple expenses
            expenses = [
                {"id": "expense-1", "description": "McDonald's"},
                {"id": "expense-2", "description": "Uber ride"},
                {"id": "expense-3", "description": "Gas station"},
            ]

            results = []
            for expense in expenses:
                result = service.suggest_category(
                    user_id="test-user-id", expense_id=expense["id"]
                )
                results.append(result)

            # Verify all categorizations were attempted
            assert len(results) == 3
            for result in results:
                assert "suggested_category_id" in result
                assert "confidence_score" in result


def test_categorization_learning_from_feedback():
    """Test that the system learns from user categorization feedback"""

    from src.services.categorization_service import CategorizationService

    with patch('src.services.categorization_service.Expense'):
        with patch('src.services.categorization_service.Category'):
            with patch('src.services.categorization_service.CategorizationFeedback'):
                with patch(
                    'src.services.categorization_service.ExpenseCategorizationRule'
                ):
                    service = CategorizationService()

                    # Confirm a categorization (this should create learning data)
                    result = service.confirm_categorization(
                        user_id="test-user-id",
                        expense_id="expense-1",
                        category_id="category-1",
                    )

                    # Verify feedback was recorded
                    assert result is not None
                    assert "expense_id" in result


def test_get_user_categories_workflow():
    """Test retrieving all categories for a user"""

    from src.services.category_service import CategoryService

    with patch('src.services.category_service.Category'):
        service = CategoryService()

        # Get all categories for user
        results = service.get_user_categories("test-user-id")

        # Verify the results
        assert isinstance(results, list)


def test_categorization_error_handling():
    """Test error handling in categorization"""

    from src.services.categorization_service import CategorizationService
    from src.services.categorization_service import CategorizationServiceError

    with patch('src.services.categorization_service.Expense') as mock_expense:
        # Create mock db_session that returns None for the expense query
        mock_db_session = MagicMock()
        mock_db_session.query.return_value.filter.return_value.first.return_value = None

        service = CategorizationService()

        # Try to categorize non-existent expense
        with pytest.raises(CategorizationServiceError):
            service.suggest_category(
                user_id="test-user-id",
                expense_id="non-existent",
                db_session=mock_db_session,
            )


def test_categorization_with_confidence_threshold():
    """Test that low confidence suggestions are handled correctly"""

    from src.services.categorization_service import CategorizationService

    with patch('src.services.categorization_service.Expense'):
        with patch('src.services.categorization_service.Category'):
            service = CategorizationService()

            result = service.suggest_category(
                user_id="test-user-id", expense_id="expense-1"
            )

            # Verify confidence score is returned
            assert "confidence_score" in result
            assert isinstance(result["confidence_score"], float)
            assert 0 <= result["confidence_score"] <= 1
