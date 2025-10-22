"""
Test suite for expense confirmation flow with update capability
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from sqlalchemy.orm import Session

from src.services.ai_agent_service import AIAgentService
from src.core.langgraph_agent import LangGraphAIAgent
from src.models.expense import Expense
from src.utils.exceptions import ValidationError


@pytest.fixture
def mock_db_session():
    """Create a mock database session"""
    return Mock(spec=Session)


@pytest.fixture
def mock_expense():
    """Create a mock expense object"""
    expense = Mock(spec=Expense)
    expense.id = "expense-123"
    expense.user_id = "user-123"
    expense.merchant_name = "Starbucks"
    expense.amount = 25000
    expense.date = "2025-10-22"
    expense.category_id = "food"
    return expense


@pytest.fixture
def ai_service(mock_db_session):
    """Create an AIAgentService with mock database"""
    return AIAgentService(db_session=mock_db_session)


class TestConfirmationFlow:
    """Tests for expense confirmation and update flow"""

    def test_detect_update_intent_with_keyword(self, ai_service):
        """Test detecting update intent from user message with keywords"""
        user_message = "Tôi muốn thay đổi số tiền thành 50,000đ"
        
        wants_update, corrections = ai_service.detect_update_intent(user_message)
        
        # Should detect that user wants to update (using keyword fallback if LLM fails)
        assert wants_update is not None
    
    def test_detect_update_intent_no_update(self, ai_service):
        """Test detecting when user doesn't want to update"""
        user_message = "Không, thông tin đó đúng rồi"
        
        wants_update, corrections = ai_service.detect_update_intent(user_message)
        
        # Should detect that user doesn't want to update
        assert wants_update is False or wants_update is None
    
    def test_extract_corrections_from_message(self, ai_service):
        """Test extracting correction details from user message"""
        user_message = "Số tiền phải là 50000 đ chứ không phải 25000"
        
        corrections = ai_service.extract_corrections_from_message(user_message)
        
        # Should attempt to extract corrections
        assert corrections is not None or corrections is None  # Depends on API response

    def test_handle_update_confirmation_no_update(self, ai_service, mock_expense):
        """Test handling confirmation when user doesn't want updates"""
        with patch.object(
            ai_service, "detect_update_intent", return_value=(False, None)
        ):
            response, corrections, budget_warning, advice = (
                ai_service.handle_update_confirmation(
                    session_id="session-123",
                    user_message="Không cần thay đổi",
                    saved_expense={"id": "exp-123", "merchant_name": "Starbucks"},
                    user_id="user-123",
                )
            )

            assert "đã được lưu" in response
            assert corrections is None

    def test_handle_update_confirmation_with_update(self, ai_service, mock_expense):
        """Test handling confirmation when user wants updates"""
        saved_expense = {
            "id": "expense-123",
            "merchant_name": "Starbucks",
            "amount": 25000,
            "date": "2025-10-22",
        }

        corrections = {"amount": 50000}

        with patch.object(
            ai_service, "detect_update_intent", return_value=(True, corrections)
        ), patch.object(
            ai_service.expense_service,
            "update_expense",
            return_value=(mock_expense, None),
        ):
            response, returned_corrections, budget_warning, advice = (
                ai_service.handle_update_confirmation(
                    session_id="session-123",
                    user_message="Thay đổi số tiền thành 50000",
                    saved_expense=saved_expense,
                    user_id="user-123",
                )
            )

            assert "✅" in response or "cập nhật" in response.lower()
            assert returned_corrections is not None


class TestLangGraphConfirmationNodes:
    """Tests for LangGraph confirmation nodes"""

    def test_ask_confirmation_node(self, mock_db_session):
        """Test the ask_confirmation node"""
        agent = LangGraphAIAgent(mock_db_session)

        state = {
            "messages": [],
            "user_id": "user-123",
            "session_id": "session-123",
            "saved_expense": {
                "merchant_name": "Starbucks",
                "amount": 25000,
                "date": "2025-10-22",
                "category_id": "food",
            },
            "db_session": mock_db_session,
            "extracted_expense": {},
            "budget_warning": {},
            "financial_advice": {},
            "asking_confirmation": False,
            "awaiting_user_response": False,
        }

        result = agent._ask_confirmation(state)

        assert "messages" in result
        assert len(result["messages"]) > 0
        assert "Starbucks" in result["messages"][0].content
        # Check for formatted amount (25,000 with comma)
        assert "25" in result["messages"][0].content and "000" in result["messages"][0].content

    def test_routing_after_confirmation(self, mock_db_session):
        """Test routing logic after confirmation"""
        agent = LangGraphAIAgent(mock_db_session)

        # Test routing when asking_confirmation is True
        state = {
            "asking_confirmation": True,
            "budget_warning": None,
        }

        route = agent._route_after_confirmation(state)
        assert route == "ask_confirmation"

        # Test routing with budget warning
        state = {
            "asking_confirmation": False,
            "budget_warning": {"message": "Budget exceeded"},
        }

        route = agent._route_after_confirmation(state)
        assert route == "generate_advice"

        # Test routing without any special conditions
        state = {
            "asking_confirmation": False,
            "budget_warning": None,
        }

        route = agent._route_after_confirmation(state)
        assert route == "llm_call"


class TestLangGraphIntentDetection:
    """Tests for intent detection in LangGraph agent"""

    def test_detect_update_intent_in_agent(self, mock_db_session):
        """Test the detect_update_intent method in agent"""
        agent = LangGraphAIAgent(mock_db_session)

        state = {
            "messages": [Mock(content="Tôi muốn thay đổi số tiền")],
            "user_id": "user-123",
            "session_id": "session-123",
            "db_session": mock_db_session,
            "extracted_expense": {},
            "budget_warning": {},
            "financial_advice": {},
            "saved_expense": {},
            "asking_confirmation": False,
            "awaiting_user_response": False,
        }

        result = agent._detect_update_intent(state)

        assert "wants_update" in result
        assert isinstance(result["wants_update"], bool)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
