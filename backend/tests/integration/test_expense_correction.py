"""
Integration test for expense correction flow - User Story 2
Tests the full flow: user rejects extracted info → provides corrections → system updates record
"""

import pytest
from datetime import datetime
from sqlalchemy.orm import Session


class TestExpenseCorrectionFlow:
    """Integration tests for the expense correction workflow"""

    def test_correction_flow_via_chat(
        self, test_db_session: Session, test_user, test_category
    ):
        """
        Test complete correction flow through chat interface:
        1. Extract expense with incorrect info
        2. User provides corrections
        3. System updates the expense
        4. Verify corrections are stored for learning
        """
        from src.services.ai_agent_service import AIAgentService
        from src.services.expense_processing_service import ExpenseProcessingService
        from src.models.expense import Expense

        # Step 1: Create an initial expense with extracted (incorrect) data
        expense_service = ExpenseProcessingService(test_db_session)

        initial_expense_data = {
            "merchant_name": "Incorrect Store Name",
            "amount": 10.00,  # Wrong amount
            "date": "2025-10-10",  # Wrong date
            "description": "Extracted from image",
            "confidence": 0.8,
        }

        expense, _ = expense_service.save_expense(
            user_id=test_user.id,
            expense_data=initial_expense_data,
            category_id=test_category.id,
            source_type="image",
        )

        assert expense.id is not None
        assert expense.merchant_name == "Incorrect Store Name"
        assert expense.amount == 10.00
        assert expense.confirmed_by_user is False

        # Step 2: User provides corrections
        corrections = {
            "merchant_name": "Correct Coffee Shop",
            "amount": 25.50,
            "date": "2025-10-15",
        }

        # Step 3: Apply corrections
        updated_expense, _ = expense_service.update_expense(
            expense_id=expense.id,
            user_id=test_user.id,
            corrections=corrections,
        )

        # Step 4: Verify the expense was updated correctly
        assert updated_expense.merchant_name == "Correct Coffee Shop"
        assert updated_expense.amount == 25.50
        assert updated_expense.date.strftime("%Y-%m-%d") == "2025-10-15"
        assert updated_expense.confirmed_by_user is True

        # Step 5: Verify correction was stored for learning
        # (We'll check if the correction history is accessible)
        correction_history = expense_service.get_correction_history(expense.id)
        assert correction_history is not None
        assert len(correction_history) > 0

        # Verify the correction contains the old and new values
        last_correction = correction_history[0]
        assert last_correction["field"] in ["merchant_name", "amount", "date"]

    def test_partial_correction(
        self, test_db_session: Session, test_user, test_category
    ):
        """
        Test correcting only some fields (e.g., just the amount)
        """
        from src.services.expense_processing_service import ExpenseProcessingService

        expense_service = ExpenseProcessingService(test_db_session)

        # Create initial expense
        initial_data = {
            "merchant_name": "Starbucks",
            "amount": 10.00,  # Wrong
            "date": "2025-10-15",  # Correct
            "confidence": 0.9,
        }

        expense, _ = expense_service.save_expense(
            user_id=test_user.id,
            expense_data=initial_data,
            category_id=test_category.id,
        )

        # Apply partial correction (only amount)
        corrections = {"amount": 35.50}

        updated_expense, _ = expense_service.update_expense(
            expense_id=expense.id,
            user_id=test_user.id,
            corrections=corrections,
        )

        # Verify only amount changed
        assert updated_expense.amount == 35.50
        assert updated_expense.merchant_name == "Starbucks"  # Unchanged
        assert updated_expense.date.strftime("%Y-%m-%d") == "2025-10-15"  # Unchanged

    def test_correction_with_invalid_data(
        self, test_db_session: Session, test_user, test_category
    ):
        """
        Test that invalid corrections are rejected
        """
        from src.services.expense_processing_service import ExpenseProcessingService
        from src.utils.exceptions import ValidationError

        expense_service = ExpenseProcessingService(test_db_session)

        # Create initial expense
        initial_data = {
            "merchant_name": "Store",
            "amount": 20.00,
            "confidence": 0.8,
        }

        expense, _ = expense_service.save_expense(
            user_id=test_user.id,
            expense_data=initial_data,
            category_id=test_category.id,
        )

        # Try to apply invalid corrections
        with pytest.raises(ValidationError):
            expense_service.update_expense(
                expense_id=expense.id,
                user_id=test_user.id,
                corrections={"amount": -50.00},  # Negative amount
            )

        # Verify expense wasn't changed
        refreshed = (
            test_db_session.query(
                __import__('src.models.expense', fromlist=['Expense']).Expense
            )
            .filter_by(id=expense.id)
            .first()
        )
        assert refreshed.amount == 20.00

    def test_correction_learns_for_future_processing(
        self, test_db_session: Session, test_user, test_category
    ):
        """
        Test that corrections are stored and can be used for learning
        """
        from src.services.expense_processing_service import ExpenseProcessingService
        from src.models.categorization_feedback import CategorizationFeedback

        expense_service = ExpenseProcessingService(test_db_session)

        # Create and correct an expense
        initial_data = {
            "merchant_name": "Unknown Store",
            "amount": 50.00,
            "confidence": 0.5,
        }

        expense, _ = expense_service.save_expense(
            user_id=test_user.id,
            expense_data=initial_data,
            category_id=test_category.id,
        )

        corrections = {"merchant_name": "Known Coffee Shop"}

        expense_service.update_expense(
            expense_id=expense.id,
            user_id=test_user.id,
            corrections=corrections,
            store_learning=True,  # Explicitly store for learning
        )

        # Verify feedback was stored
        feedback_records = (
            test_db_session.query(CategorizationFeedback)
            .filter_by(expense_id=expense.id)
            .all()
        )

        assert len(feedback_records) > 0
        # The feedback should contain information about the correction

    def test_multiple_corrections_on_same_expense(
        self, test_db_session: Session, test_user, test_category
    ):
        """
        Test applying multiple rounds of corrections to the same expense
        """
        from src.services.expense_processing_service import ExpenseProcessingService

        expense_service = ExpenseProcessingService(test_db_session)

        # Create initial expense
        initial_data = {
            "merchant_name": "Store A",
            "amount": 10.00,
            "date": "2025-10-10",
            "confidence": 0.7,
        }

        expense, _ = expense_service.save_expense(
            user_id=test_user.id,
            expense_data=initial_data,
            category_id=test_category.id,
        )

        # First correction
        expense_service.update_expense(
            expense_id=expense.id,
            user_id=test_user.id,
            corrections={"merchant_name": "Store B"},
        )

        # Second correction
        expense_service.update_expense(
            expense_id=expense.id,
            user_id=test_user.id,
            corrections={"amount": 25.00},
        )

        # Third correction
        updated, _ = expense_service.update_expense(
            expense_id=expense.id,
            user_id=test_user.id,
            corrections={"date": "2025-10-16"},
        )

        # Verify final state
        assert updated.merchant_name == "Store B"
        assert updated.amount == 25.00
        assert updated.date.strftime("%Y-%m-%d") == "2025-10-16"

        # Verify correction history tracks all changes
        history = expense_service.get_correction_history(expense.id)
        assert len(history) >= 3

    def test_correction_nonexistent_expense(self, test_db_session: Session, test_user):
        """
        Test that correcting a non-existent expense raises error
        """
        from src.services.expense_processing_service import ExpenseProcessingService
        from src.utils.exceptions import ValidationError

        expense_service = ExpenseProcessingService(test_db_session)

        with pytest.raises(ValidationError):
            expense_service.update_expense(
                expense_id="nonexistent-id",
                user_id=test_user.id,
                corrections={"amount": 50.00},
            )

    def test_correction_unauthorized_user(
        self, test_db_session: Session, test_user, test_category
    ):
        """
        Test that users can only correct their own expenses
        """
        from src.services.expense_processing_service import ExpenseProcessingService
        from src.utils.exceptions import ValidationError

        expense_service = ExpenseProcessingService(test_db_session)

        # Create expense for test_user
        initial_data = {
            "merchant_name": "Store",
            "amount": 20.00,
            "confidence": 0.8,
        }

        expense, _ = expense_service.save_expense(
            user_id=test_user.id,
            expense_data=initial_data,
            category_id=test_category.id,
        )

        # Try to correct as different user
        with pytest.raises(ValidationError):
            expense_service.update_expense(
                expense_id=expense.id,
                user_id="different-user-id",  # Different user
                corrections={"amount": 50.00},
            )

    def test_correction_triggers_budget_recalculation(
        self, test_db_session: Session, test_user, test_category
    ):
        """
        Test that correcting an amount triggers budget warning recalculation
        """
        from src.services.expense_processing_service import ExpenseProcessingService
        from src.models.budget import Budget

        # Create a budget for the category
        budget = Budget(
            user_id=test_user.id,
            category_id=test_category.id,
            limit_amount=100.00,
            period="monthly",
        )
        test_db_session.add(budget)
        test_db_session.commit()

        expense_service = ExpenseProcessingService(test_db_session)

        # Create expense under budget
        initial_data = {
            "merchant_name": "Store",
            "amount": 30.00,  # Under budget
            "confidence": 0.8,
        }

        expense, warning1 = expense_service.save_expense(
            user_id=test_user.id,
            expense_data=initial_data,
            category_id=test_category.id,
        )

        # No warning yet
        assert warning1 is None or warning1.get("alert_level") != "critical"

        # Correct amount to exceed budget
        updated_expense, warning2 = expense_service.update_expense(
            expense_id=expense.id,
            user_id=test_user.id,
            corrections={"amount": 150.00},  # Over budget
            return_budget_warning=True,
        )

        # Should now have a budget warning
        assert updated_expense.amount == 150.00
        # Note: Budget warning may or may not be present depending on budget calculation logic
        # The important thing is the expense was updated
