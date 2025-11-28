
import pytest
from sqlalchemy.orm import Session

class TestCategoryCorrectionFlow:
    """Integration tests for the category correction workflow"""

    def test_category_correction_flow(
        self, test_db_session: Session, test_user, test_category
    ):
        """
        Test correcting the category of an expense through chat interface logic
        """
        from src.services.expense_processing_service import ExpenseProcessingService
        from src.models.category import Category
        
        # Create another category to switch to
        new_category = Category(
            user_id=test_user.id,
            name="New Category",
            description="For testing correction",
            icon="🔄"
        )
        test_db_session.add(new_category)
        test_db_session.commit()
        
        expense_service = ExpenseProcessingService(test_db_session)

        # Step 1: Create an initial expense
        initial_expense_data = {
            "merchant_name": "Test Store",
            "amount": 100.00,
            "date": "2025-11-28",
            "description": "Test expense",
            "confidence": 0.9,
        }

        expense, _ = expense_service.save_expense(
            user_id=test_user.id,
            expense_data=initial_expense_data,
            category_id=test_category.id,
            source_type="text",
        )

        assert expense.category_id == test_category.id

        # Step 2: Apply corrections (simulating what the agent would do after extraction)
        # The agent should extract "New Category" and map it to new_category.id
        
        # We'll test the service update directly first to ensure service layer works
        corrections = {
            "category_id": str(new_category.id)
        }

        updated_expense, _ = expense_service.update_expense(
            expense_id=expense.id,
            user_id=test_user.id,
            corrections=corrections,
        )

        # Step 3: Verify update
        assert updated_expense.category_id == new_category.id
        
    def test_date_correction_flow(
        self, test_db_session: Session, test_user, test_category
    ):
        """
        Test correcting the date of an expense
        """
        from src.services.expense_processing_service import ExpenseProcessingService
        from datetime import datetime
        
        expense_service = ExpenseProcessingService(test_db_session)

        # Step 1: Create an initial expense
        initial_expense_data = {
            "merchant_name": "Test Store",
            "amount": 100.00,
            "date": "2025-11-28",
            "description": "Test expense",
            "confidence": 0.9,
        }

        expense, _ = expense_service.save_expense(
            user_id=test_user.id,
            expense_data=initial_expense_data,
            category_id=test_category.id,
        )

        # Step 2: Apply date correction
        new_date = "2025-12-01"
        corrections = {
            "date": new_date
        }

        updated_expense, _ = expense_service.update_expense(
            expense_id=expense.id,
            user_id=test_user.id,
            corrections=corrections,
        )

        # Step 3: Verify update
        assert updated_expense.date.strftime("%Y-%m-%d") == new_date
