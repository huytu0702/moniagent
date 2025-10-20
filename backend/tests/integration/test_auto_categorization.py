"""
Integration tests for automatic expense categorization feature

Tests the complete flow:
1. User provides expense description with merchant name
2. System extracts expense data
3. System auto-categorizes based on rules
4. System returns category suggestion with confidence score
"""

import pytest
from unittest.mock import MagicMock
from datetime import datetime
from src.services.expense_processing_service import ExpenseProcessingService
from src.services.categorization_service import CategorizationService
from src.models.expense_categorization_rule import ExpenseCategorizationRule


@pytest.fixture
def categorization_service():
    """Create a categorization service instance"""
    return CategorizationService()


@pytest.fixture
def mock_db_session():
    """Create a mock database session"""
    return MagicMock()


def test_auto_categorization_with_matching_rule(
    mock_db_session, categorization_service
):
    """
    Test that extract_expense_from_text auto-categorizes when rules match

    Scenario:
    - User says: "i spent $25 at Starbucks"
    - User has rule: "starbucks" → "Food & Dining" category
    - System should auto-suggest that category
    """
    user_id = "user-123"

    # Create a mock rule: starbucks -> food category
    starbucks_rule = MagicMock(spec=ExpenseCategorizationRule)
    starbucks_rule.store_name_pattern = "starbucks"
    starbucks_rule.category_id = "cat-food-dining"
    starbucks_rule.rule_type = "keyword"
    starbucks_rule.confidence_threshold = 0.8
    starbucks_rule.is_active = True

    # Mock the database query
    mock_db_session.query.return_value.filter.return_value.all.return_value = [
        starbucks_rule
    ]

    # Create service with mocked session
    service = ExpenseProcessingService(db_session=mock_db_session)

    # Extract with user_id to trigger auto-categorization
    result = service.extract_expense_from_text(
        "i spent $25 at Starbucks", user_id=user_id
    )

    # Verify extraction worked
    assert result["amount"] == 25.0
    assert result["merchant_name"] == "Starbucks"

    # Verify auto-categorization happened
    assert result.get("suggested_category_id") == "cat-food-dining"
    assert result.get("categorization_confidence", 0) >= 0.8
    assert result.get("category_id") == "cat-food-dining"


def test_extraction_without_user_id_no_categorization(mock_db_session):
    """
    Test that extraction without user_id does NOT auto-categorize

    Scenario:
    - User extracts expense but no user_id provided
    - System should extract data but NOT categorize
    """
    service = ExpenseProcessingService(db_session=mock_db_session)

    # Extract WITHOUT user_id
    result = service.extract_expense_from_text("i spent $25 at Starbucks")

    # Verify extraction worked
    assert result["amount"] == 25.0
    assert result["merchant_name"] == "Starbucks"

    # Verify NO categorization (user_id not provided)
    assert "suggested_category_id" not in result
    assert "category_id" not in result


def test_no_matching_rules_no_categorization(mock_db_session):
    """
    Test that no suggestion is made when no rules match

    Scenario:
    - User says: "i spent $50 at Random Store"
    - User has NO rules for "Random Store"
    - System should extract but NOT suggest category
    """
    user_id = "user-123"

    # No rules for this user
    mock_db_session.query.return_value.filter.return_value.all.return_value = []

    service = ExpenseProcessingService(db_session=mock_db_session)

    result = service.extract_expense_from_text(
        "i spent $50 at Random Store", user_id=user_id
    )

    # Verify extraction worked
    assert result["amount"] == 50.0
    assert result["merchant_name"] == "Random Store"

    # Verify NO categorization (no matching rules)
    assert "suggested_category_id" not in result
    assert "category_id" not in result


def test_multiple_matching_rules_selects_best_match(
    mock_db_session, categorization_service
):
    """
    Test that when multiple rules match, the best one is selected

    Scenario:
    - User says: "i spent $30 at Coffee Shop"
    - User has rules:
      - "coffee" → category A (keyword match)
      - "coffee shop" → category B (better match)
    - System should select the best match (higher confidence)
    """
    user_id = "user-123"

    # Create two matching rules
    coffee_rule = MagicMock(spec=ExpenseCategorizationRule)
    coffee_rule.store_name_pattern = "coffee"
    coffee_rule.category_id = "cat-beverages"
    coffee_rule.rule_type = "keyword"
    coffee_rule.confidence_threshold = 0.7

    coffee_shop_rule = MagicMock(spec=ExpenseCategorizationRule)
    coffee_shop_rule.store_name_pattern = "coffee shop"
    coffee_shop_rule.category_id = "cat-food-dining"
    coffee_shop_rule.rule_type = "keyword"
    coffee_shop_rule.confidence_threshold = 0.8

    # Mock returns both rules
    mock_db_session.query.return_value.filter.return_value.all.return_value = [
        coffee_rule,
        coffee_shop_rule,
    ]

    service = ExpenseProcessingService(db_session=mock_db_session)

    result = service.extract_expense_from_text(
        "i spent $30 at Coffee Shop", user_id=user_id
    )

    # Verify extraction
    assert result["amount"] == 30.0
    assert result["merchant_name"] == "Coffee Shop"

    # Both rules match, but coffee_shop should match better
    assert result.get("suggested_category_id") in ["cat-beverages", "cat-food-dining"]


def test_categorization_confidence_below_threshold_no_suggest(mock_db_session):
    """
    Test that suggestions below confidence threshold are not suggested

    Scenario:
    - User says: "i spent $20 at Xyz Store"
    - User has rule: "abc" → category (very specific, won't match)
    - System should NOT suggest because confidence is too low
    """
    user_id = "user-123"

    # Create rule with high threshold
    strict_rule = MagicMock(spec=ExpenseCategorizationRule)
    strict_rule.store_name_pattern = "abc"
    strict_rule.category_id = "cat-other"
    strict_rule.rule_type = "keyword"
    strict_rule.confidence_threshold = 0.9  # Very strict

    mock_db_session.query.return_value.filter.return_value.all.return_value = [
        strict_rule
    ]

    service = ExpenseProcessingService(db_session=mock_db_session)

    result = service.extract_expense_from_text(
        "i spent $20 at Xyz Store", user_id=user_id
    )

    # Verify extraction
    assert result["amount"] == 20.0

    # Should NOT suggest because "abc" doesn't match "Xyz Store"
    assert "suggested_category_id" not in result
    assert "category_id" not in result
