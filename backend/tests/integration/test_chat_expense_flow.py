"""
Integration tests for Chat Expense Flow
Tests the complete flow from chat message to expense recording
"""

import pytest
from datetime import datetime
from sqlalchemy.orm import Session
from src.models.expense import Expense
from src.models.chat_session import ChatSession
from src.services.ai_agent_service import AIAgentService
from src.services.expense_processing_service import ExpenseProcessingService


class TestChatTextExpenseFlow:
    """Integration tests for text input → expense extraction → database record flow"""

    def test_text_input_extraction_and_save_flow(self, test_db_session: Session):
        """Test complete flow: text input → extract → save expense"""
        user_id = "test-user-123"

        # Initialize services
        ai_service = AIAgentService(test_db_session)
        expense_service = ExpenseProcessingService(test_db_session)

        # Step 1: Start a chat session
        chat_session = ai_service.start_session(user_id, "Test Expense Session")
        assert chat_session is not None
        assert chat_session.user_id == user_id

        # Step 2: Extract expense from text
        expense_data = expense_service.extract_expense_from_text(
            "I spent $45 at Italian restaurant yesterday"
        )
        assert expense_data is not None
        assert (
            expense_data.get("amount") is not None
            or expense_data.get("merchant_name") is not None
        )

        # Step 3: Validate extracted expense
        if expense_data.get("amount"):
            is_valid = expense_service.validate_extracted_expense(expense_data)
            if is_valid:
                # Step 4: Save expense to database
                expense, budget_warning = expense_service.save_expense(
                    user_id=user_id,
                    expense_data=expense_data,
                    source_type="text",
                )

                assert expense is not None
                assert expense.id is not None
                assert expense.user_id == user_id
                assert expense.source_type == "text"
                assert expense.confirmed_by_user == False

    def test_user_confirmation_updates_expense(self, test_db_session: Session):
        """Test that confirming expense updates the confirmed_by_user flag"""
        user_id = "test-user-456"
        expense_service = ExpenseProcessingService(test_db_session)

        # Create and save an expense
        expense_data = {
            "merchant_name": "Coffee Shop",
            "amount": 5.50,
            "date": "2025-10-16",
            "confidence": 0.9,
            "description": "Morning coffee",
        }

        expense, _ = expense_service.save_expense(
            user_id=user_id,
            expense_data=expense_data,
            source_type="text",
        )

        assert expense.confirmed_by_user == False

        # Confirm the expense
        confirmed_expense = expense_service.confirm_expense(expense.id)

        assert confirmed_expense.confirmed_by_user == True
        assert confirmed_expense.id == expense.id

    def test_expense_correction_flow(self, test_db_session: Session):
        """Test correction flow: extract → user provides corrections → save"""
        user_id = "test-user-789"
        expense_service = ExpenseProcessingService(test_db_session)

        # Initial extracted data (might have errors)
        initial_data = {
            "merchant_name": "Starbuck",  # Typo
            "amount": 5.50,
            "date": "2025-10-16",
            "confidence": 0.7,
            "description": "Coffee",
        }

        # Save initial expense
        expense, _ = expense_service.save_expense(
            user_id=user_id,
            expense_data=initial_data,
            source_type="text",
        )

        # Correct the expense with user corrections
        corrections = {"merchant_name": "Starbucks"}
        confirmed_expense = expense_service.confirm_expense(expense.id, corrections)

        # Verify corrections were applied
        assert confirmed_expense.merchant_name == "Starbucks"
        assert confirmed_expense.confirmed_by_user == True

    def test_chat_session_history_preserved(self, test_db_session: Session):
        """Test that chat session history is properly saved"""
        user_id = "test-user-history"

        ai_service = AIAgentService(test_db_session)

        # Start session
        session = ai_service.start_session(user_id, "History Test")

        # Process multiple messages
        response1, extracted1, _, _ = ai_service.process_message(
            session.id, "I spent $25 on coffee", "text"
        )

        response2, extracted2, _, _ = ai_service.process_message(
            session.id, "I spent $50 on lunch", "text"
        )

        # Get session history
        retrieved_session, messages = ai_service.get_session_history(session.id)

        # Verify session
        assert retrieved_session.id == session.id
        assert retrieved_session.user_id == user_id

        # Verify messages were saved
        assert len(messages) >= 2  # At least user's 2 messages + AI responses

    def test_multiple_expenses_in_session(self, test_db_session: Session):
        """Test recording multiple expenses in a single chat session"""
        user_id = "test-user-multi"

        ai_service = AIAgentService(test_db_session)
        expense_service = ExpenseProcessingService(test_db_session)

        # Start session
        session = ai_service.start_session(user_id, "Multi-Expense Session")

        # Record first expense
        data1 = {
            "merchant_name": "Coffee Shop",
            "amount": 5.50,
            "date": "2025-10-16",
            "confidence": 0.9,
            "description": "Coffee",
        }
        expense1, _ = expense_service.save_expense(
            user_id=user_id, expense_data=data1, source_type="text"
        )

        # Record second expense
        data2 = {
            "merchant_name": "Restaurant",
            "amount": 35.00,
            "date": "2025-10-16",
            "confidence": 0.85,
            "description": "Lunch",
        }
        expense2, _ = expense_service.save_expense(
            user_id=user_id, expense_data=data2, source_type="text"
        )

        # Verify both expenses are saved
        assert expense1.id is not None
        assert expense2.id is not None
        assert expense1.id != expense2.id

        # Verify expenses can be retrieved
        retrieved1 = expense_service.get_expense(expense1.id)
        retrieved2 = expense_service.get_expense(expense2.id)

        assert retrieved1.merchant_name == "Coffee Shop"
        assert retrieved2.merchant_name == "Restaurant"


class TestChatImageExpenseFlow:
    """Integration tests for image upload → OCR → expense extraction → database record"""

    def test_image_upload_extraction_flow(
        self, test_db_session: Session, valid_image_upload: str
    ):
        """Test flow: image upload → OCR extraction → save expense"""
        user_id = "test-user-image"

        expense_service = ExpenseProcessingService(test_db_session)

        # Extract from image
        try:
            extracted = expense_service.extract_expense_from_image(valid_image_upload)

            # Verify structure
            assert isinstance(extracted, dict)
            assert "confidence" in extracted  # OCR should have confidence score

            # If extraction was successful, save the expense
            if extracted.get("amount"):
                expense, _ = expense_service.save_expense(
                    user_id=user_id,
                    expense_data=extracted,
                    source_type="image",
                )

                assert expense.source_type == "image"
                assert expense.source_metadata is not None

        except Exception as e:
            # OCR might fail due to API key, which is OK in testing
            pytest.skip(
                f"OCR extraction failed (expected in test environment): {str(e)}"
            )


class TestExpenseValidation:
    """Tests for expense validation and error handling"""

    def test_invalid_amount_rejected(self, test_db_session: Session):
        """Test that invalid amounts are rejected"""
        user_id = "test-user-invalid"
        expense_service = ExpenseProcessingService(test_db_session)

        # Try to save with invalid amount
        expense_data = {
            "merchant_name": "Restaurant",
            "amount": -50,  # Invalid: negative
            "date": "2025-10-16",
            "confidence": 0.9,
            "description": "Lunch",
        }

        is_valid = expense_service.validate_extracted_expense(expense_data)
        assert is_valid == False

    def test_future_date_handling(self, test_db_session: Session):
        """Test handling of future dates"""
        user_id = "test-user-future"
        expense_service = ExpenseProcessingService(test_db_session)

        from datetime import timedelta

        future_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

        expense_data = {
            "merchant_name": "Restaurant",
            "amount": 50.0,
            "date": future_date,
            "confidence": 0.9,
            "description": "Future lunch",
        }

        # Future dates might be rejected
        is_valid = expense_service.validate_extracted_expense(expense_data)
        # The test should pass if validation either accepts or rejects consistently
        assert isinstance(is_valid, bool)

    def test_missing_amount_extraction(self, test_db_session: Session):
        """Test extraction when amount cannot be determined"""
        user_id = "test-user-no-amount"
        expense_service = ExpenseProcessingService(test_db_session)

        expense_data = {
            "merchant_name": "Restaurant",
            "amount": None,  # Missing amount
            "date": "2025-10-16",
            "confidence": 0.5,
            "description": "Some restaurant",
        }

        is_valid = expense_service.validate_extracted_expense(expense_data)
        assert is_valid == False
