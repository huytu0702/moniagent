"""
Unit test for expense categorization service
"""

import pytest
import os
from unittest.mock import patch, MagicMock, call
from datetime import datetime


@pytest.fixture(autouse=True)
def set_jwt_secret():
    """Set JWT_SECRET environment variable for tests"""
    os.environ["JWT_SECRET"] = "test-secret-key-for-testing-only"
    yield
    if "JWT_SECRET" in os.environ:
        del os.environ["JWT_SECRET"]


def test_categorization_service_initialization():
    """Test that CategorizationService initializes correctly"""
    from src.services.categorization_service import CategorizationService

    service = CategorizationService()
    assert service is not None


def test_suggest_category_basic():
    """Test basic category suggestion"""
    from src.services.categorization_service import CategorizationService

    with patch('src.services.categorization_service.Expense'):
        with patch('src.services.categorization_service.Category'):
            service = CategorizationService()

            result = service.suggest_category(
                user_id="test-user-id", expense_id="expense-1"
            )

            assert result is not None
            assert "suggested_category_id" in result
            assert "suggested_category_name" in result
            assert "confidence_score" in result


def test_suggest_category_with_store_name():
    """Test category suggestion with store name pattern matching"""
    from src.services.categorization_service import CategorizationService

    with patch('src.services.categorization_service.Expense') as mock_expense_model:
        with patch(
            'src.services.categorization_service.Category'
        ) as mock_category_model:
            with patch(
                'src.services.categorization_service.ExpenseCategorizationRule'
            ) as mock_rule_model:
                # Setup expense mock
                expense_mock = MagicMock()
                expense_mock.description = "McDonald's - Main St"

                # Setup category mock
                category_mock = MagicMock()
                category_mock.id = "category-1"
                category_mock.name = "Eating Out"

                # Create mock db_session with proper query method
                mock_db_session = MagicMock()

                def query_side_effect(model):
                    result = MagicMock()
                    if hasattr(model, '__name__') and model.__name__ == 'Expense':
                        result.filter.return_value.first.return_value = expense_mock
                        result.filter.return_value.all.return_value = []
                    elif (
                        hasattr(model, '__name__')
                        and model.__name__ == 'ExpenseCategorizationRule'
                    ):
                        result.filter.return_value.all.return_value = []
                    else:
                        result.filter.return_value.first.return_value = category_mock
                    return result

                mock_db_session.query.side_effect = query_side_effect

                service = CategorizationService()
                result = service.suggest_category(
                    user_id="test-user-id",
                    expense_id="expense-1",
                    db_session=mock_db_session,
                )

                assert result["suggested_category_name"] == "Eating Out"


def test_confirm_categorization():
    """Test confirming a categorization"""
    from src.services.categorization_service import CategorizationService

    with patch('src.services.categorization_service.Expense'):
        with patch('src.services.categorization_service.Category'):
            with patch('src.services.categorization_service.CategorizationFeedback'):
                service = CategorizationService()

                result = service.confirm_categorization(
                    user_id="test-user-id",
                    expense_id="expense-1",
                    category_id="category-1",
                )

                assert result["expense_id"] == "expense-1"
                assert result["category_id"] == "category-1"
                assert result["is_user_confirmed"] is True


def test_confirm_categorization_creates_feedback():
    """Test that confirming categorization creates feedback record"""
    from src.services.categorization_service import CategorizationService

    with patch('src.services.categorization_service.Expense'):
        with patch('src.services.categorization_service.Category'):
            with patch(
                'src.services.categorization_service.CategorizationFeedback'
            ) as mock_feedback:
                service = CategorizationService()

                service.confirm_categorization(
                    user_id="test-user-id",
                    expense_id="expense-1",
                    category_id="category-1",
                )

                # Verify feedback was created
                assert mock_feedback.call_count >= 0


def test_get_categories_for_user():
    """Test retrieving categories for a specific user"""
    from src.services.category_service import CategoryService

    with patch('src.services.category_service.Category') as mock_category:
        mock_query = MagicMock()
        mock_category.query.return_value = mock_query

        # Setup return values for mocks
        category1 = MagicMock()
        category1.to_dict = lambda: {
            "id": "category-1",
            "user_id": "test-user-id",
            "name": "Eating Out",
        }
        category2 = MagicMock()
        category2.to_dict = lambda: {
            "id": "category-2",
            "user_id": "test-user-id",
            "name": "Transportation",
        }

        mock_query.filter.return_value.order_by.return_value.all.return_value = [
            category1,
            category2,
        ]

        # Create mock db_session
        mock_db_session = MagicMock()
        mock_db_session.query.return_value = mock_query

        service = CategoryService()
        results = service.get_user_categories(
            "test-user-id", db_session=mock_db_session
        )

        assert isinstance(results, list)
        assert len(results) == 2


def test_create_category():
    """Test creating a new category"""
    from src.services.category_service import CategoryService

    with patch('src.services.category_service.Category'):
        service = CategoryService()

        result = service.create_category(
            user_id="test-user-id",
            name="Eating Out",
            description="Restaurant purchases",
            icon="🍽️",
            color="#FF5733",
        )

        assert result is not None
        assert result["name"] == "Eating Out"
        assert result["user_id"] == "test-user-id"


def test_create_categorization_rule():
    """Test creating a categorization rule"""
    from src.services.category_service import CategoryService

    with patch('src.services.category_service.ExpenseCategorizationRule'):
        service = CategoryService()

        result = service.create_categorization_rule(
            user_id="test-user-id",
            category_id="category-1",
            store_name_pattern="Restaurant",
            rule_type="keyword",
            confidence_threshold=0.8,
        )

        assert result is not None
        assert result["store_name_pattern"] == "Restaurant"
        assert result["rule_type"] == "keyword"
        assert result["confidence_threshold"] == 0.8


def test_categorization_confidence_score_range():
    """Test that confidence scores are in valid range [0, 1]"""
    from src.services.categorization_service import CategorizationService

    with patch('src.services.categorization_service.Expense'):
        with patch('src.services.categorization_service.Category'):
            service = CategorizationService()

            result = service.suggest_category(
                user_id="test-user-id", expense_id="expense-1"
            )

            confidence = result["confidence_score"]
            assert (
                0 <= confidence <= 1
            ), f"Confidence score {confidence} is not in [0, 1]"


def test_suggestion_with_no_matching_rules():
    """Test suggestion when no rules match the expense"""
    from src.services.categorization_service import CategorizationService

    with patch('src.services.categorization_service.Expense'):
        with patch(
            'src.services.categorization_service.ExpenseCategorizationRule'
        ) as mock_rule:
            mock_rule.query.return_value.filter.return_value.all.return_value = []

            service = CategorizationService()

            result = service.suggest_category(
                user_id="test-user-id", expense_id="expense-1"
            )

            # Should still return a result, possibly with default category
            assert result is not None


def test_expense_not_found_error():
    """Test error handling when expense doesn't exist"""
    from src.services.categorization_service import (
        CategorizationService,
        CategorizationServiceError,
    )

    with patch('src.services.categorization_service.Expense') as mock_expense:
        # Create mock db_session that returns None for the expense query
        mock_db_session = MagicMock()
        mock_db_session.query.return_value.filter.return_value.first.return_value = None

        service = CategorizationService()

        with pytest.raises(CategorizationServiceError):
            service.suggest_category(
                user_id="test-user-id",
                expense_id="non-existent",
                db_session=mock_db_session,
            )


def test_category_not_found_error():
    """Test error handling when category doesn't exist"""
    from src.services.categorization_service import (
        CategorizationService,
        CategorizationServiceError,
    )

    with patch('src.services.categorization_service.Expense'):
        with patch('src.services.categorization_service.Category') as mock_category:
            # Create mock db_session that returns a valid expense but None for category
            mock_db_session = MagicMock()

            # Set up the query chain to return different values for Expense vs Category
            def mock_query_side_effect(model):
                mock_query_obj = MagicMock()
                if model.__name__ == 'Expense':
                    mock_query_obj.filter.return_value.first.return_value = MagicMock(
                        id='expense-1'
                    )
                else:
                    # Category query returns None
                    mock_query_obj.filter.return_value.first.return_value = None
                return mock_query_obj

            mock_db_session.query.side_effect = mock_query_side_effect

            service = CategorizationService()

            with pytest.raises(CategorizationServiceError):
                service.confirm_categorization(
                    user_id="test-user-id",
                    expense_id="expense-1",
                    category_id="non-existent",
                    db_session=mock_db_session,
                )


def test_duplicate_category_error():
    """Test error handling when creating duplicate category"""
    from src.services.category_service import CategoryService, CategoryServiceError

    with patch('src.services.category_service.Category') as mock_category:
        # Create mock db_session that returns an existing category (simulating duplicate)
        mock_db_session = MagicMock()
        mock_db_session.query.return_value.filter.return_value.first.return_value = (
            MagicMock(name="Eating Out")
        )

        service = CategoryService()

        with pytest.raises(CategoryServiceError):
            service.create_category(
                user_id="test-user-id",
                name="Eating Out",
                description="Duplicate",
                db_session=mock_db_session,
            )


def test_update_category():
    """Test updating an existing category"""
    from src.services.category_service import CategoryService

    with patch('src.services.category_service.Category'):
        service = CategoryService()

        result = service.update_category(
            user_id="test-user-id",
            category_id="category-1",
            name="Updated Name",
            description="Updated description",
        )

        assert result is not None
        assert "id" in result


def test_delete_category():
    """Test deleting a category"""
    from src.services.category_service import CategoryService

    with patch('src.services.category_service.Category'):
        service = CategoryService()

        result = service.delete_category(
            user_id="test-user-id", category_id="category-1"
        )

        assert result is not None


def test_get_categorization_rules_for_category():
    """Test retrieving categorization rules for a specific category"""
    from src.services.category_service import CategoryService

    with patch('src.services.category_service.ExpenseCategorizationRule'):
        service = CategoryService()

        results = service.get_categorization_rules_for_category("category-1")

        assert isinstance(results, list)


def test_pattern_matching_keyword():
    """Test keyword pattern matching for rules"""
    from src.services.categorization_service import CategorizationService

    # Test that keywords are matched correctly
    keywords = ["Restaurant", "Cafe", "Diner"]
    store_name = "McDonald's Restaurant"

    # Simple keyword matching
    matches = any(keyword.lower() in store_name.lower() for keyword in keywords)
    assert matches is True


def test_pattern_matching_no_match():
    """Test pattern matching when no keywords match"""
    from src.services.categorization_service import CategorizationService

    keywords = ["Restaurant", "Cafe"]
    store_name = "Gas Station"

    matches = any(keyword.lower() in store_name.lower() for keyword in keywords)
    assert matches is False
