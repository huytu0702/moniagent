"""
AI Agent Service using LangGraph for managing expense tracking conversations
"""

import logging
import json
from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime
from sqlalchemy.orm import Session

from src.core.langgraph_agent import LangGraphAIAgent
from src.services.expense_processing_service import ExpenseProcessingService
from src.services.budget_management_service import BudgetManagementService
from src.services.financial_advice_service import FinancialAdviceService
from src.models.expense import Expense
from src.models.chat_session import ChatSession, ChatMessage
from src.models.category import Category
from src.utils.exceptions import ValidationError

logger = logging.getLogger(__name__)


class AIAgentService:
    """
    Service for managing AI-powered expense tracking conversations using LangGraph
    """

    def __init__(self, db_session: Session = None):
        self.db_session = db_session
        self.expense_service = ExpenseProcessingService(db_session)
        self.budget_service = BudgetManagementService(db_session)
        self.advice_service = FinancialAdviceService()
        self.langgraph_agent = None

        if db_session:
            self.langgraph_agent = LangGraphAIAgent(db_session)

    def get_user_categories(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get all categories for a user to use in LLM prompts

        Args:
            user_id: User ID

        Returns:
            List of category dictionaries
        """
        if not self.db_session:
            return []

        categories = (
            self.db_session.query(Category)
            .filter(Category.user_id == user_id)
            .order_by(Category.display_order)
            .all()
        )

        return [
            {
                "id": str(cat.id),
                "name": cat.name,
                "description": cat.description,
                "icon": cat.icon,
            }
            for cat in categories
        ]

    def categorize_expense_with_llm(
        self, user_id: str, merchant_name: str, description: str, amount: float
    ) -> Tuple[Optional[str], Optional[float]]:
        """
        Use LLM to categorize an expense into one of user's categories

        Args:
            user_id: User ID
            merchant_name: Merchant/store name
            description: Expense description
            amount: Expense amount

        Returns:
            Tuple of (category_id, confidence_score)
        """
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            from langchain_core.messages import HumanMessage

            # Get user's categories
            categories = self.get_user_categories(user_id)
            if not categories:
                logger.warning(f"No categories found for user {user_id}")
                return None, None

            # Build category list for prompt
            category_list = "\n".join(
                [
                    f"- {cat['name']} ({cat['icon']}): {cat['description']} [ID: {cat['id']}]"
                    for cat in categories
                ]
            )

            # Create detailed categorization prompt
            prompt = f"""Bạn là một chuyên gia phân loại chi tiêu. Dựa trên thông tin chi tiêu dưới đây, hãy phân loại vào một trong các danh mục sau:

{category_list}

**Thông tin chi tiêu:**
- Nơi/Cửa hàng: {merchant_name}
- Mô tả: {description}
- Số tiền: {amount}

**Yêu cầu:**
1. Phân loại vào danh mục phù hợp nhất
2. Đưa ra độ tin cậy từ 0.0 đến 1.0 (1.0 là hoàn toàn chắc chắn)
3. Trả về JSON format: {{"category_id": "ID danh mục", "category_name": "Tên danh mục", "confidence": 0.0-1.0, "reasoning": "Lý do phân loại"}}

**Hướng dẫn phân loại:**
- "Ăn uống": Cơm, cà phê, nhà hàng, quán ăn, siêu thị (thực phẩm)
- "Đi lại": Grab, Uber, Taxi, xăng xe, bảo dưỡng, vé xe
- "Nhà ở": Thuê nhà, tiền điện, nước, internet, wifi
- "Mua sắm cá nhân": Quần áo, giày, mỹ phẩm, điện thoại, laptop
- "Giải trí & du lịch": Phim, game, du lịch, khách sạn, vé máy bay, Netflix
- "Giáo dục & học tập": Học phí, sách, khóa học online
- "Sức khỏe & thể thao": Thuốc, bệnh viện, gym, yoga
- "Gia đình & quà tặng": Quà tặng, lễ tết, sinh nhật
- "Đầu tư & tiết kiệm": Cổ phiếu, gửi tiết kiệm, ngân hàng
- "Khác": Các chi phí không thuộc nhóm trên

Hãy trả về JSON không có markdown:"""

            # Initialize LLM
            model = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.1)

            # Get LLM response
            response = model.invoke([HumanMessage(content=prompt)])
            response_text = response.content.strip()

            logger.info(f"LLM categorization response: {response_text}")

            # Parse JSON response
            try:
                # Clean up markdown if present
                if "```json" in response_text:
                    response_text = (
                        response_text.split("```json")[1].split("```")[0].strip()
                    )
                elif "```" in response_text:
                    response_text = (
                        response_text.split("```")[1].split("```")[0].strip()
                    )

                result = json.loads(response_text)

                category_id = result.get("category_id")
                confidence = result.get("confidence", 0.5)
                reasoning = result.get("reasoning", "")

                logger.info(
                    f"LLM categorized expense: {result.get('category_name')} (confidence: {confidence})"
                )

                return category_id, confidence

            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse LLM response: {str(e)}")
                logger.error(f"Response was: {response_text}")
                return None, None

        except Exception as e:
            logger.error(f"Error categorizing with LLM: {str(e)}")
            return None, None

    def start_session(
        self, user_id: str, session_title: Optional[str] = None
    ) -> ChatSession:
        """
        Start a new chat session

        Args:
            user_id: User ID
            session_title: Optional session title

        Returns:
            ChatSession object
        """
        if not self.db_session:
            raise ValueError("Database session not available")

        session = ChatSession(
            user_id=user_id,
            session_title=session_title or "Expense Tracking Session",
        )

        self.db_session.add(session)
        self.db_session.commit()
        self.db_session.refresh(session)

        logger.info(f"Chat session started: {session.id}")
        return session

    def get_initial_message(self) -> str:
        """
        Get the initial greeting message

        Returns:
            Initial message string
        """
        return (
            "Hello! I'm your AI assistant for expense tracking. You can:\n"
            "1. Upload an invoice image for me to extract the details\n"
            "2. Type out your expense (e.g., 'I spent $25 at Starbucks')\n\n"
            "What would you like to do?"
        )

    def process_message(
        self, session_id: str, user_message: str, message_type: str = "text"
    ) -> Tuple[
        str,
        Optional[Dict[str, Any]],
        Optional[Dict[str, Any]],
        Optional[Dict[str, Any]],
    ]:
        """
        Process a user message using LangGraph AI agent and generate a response

        Args:
            session_id: Chat session ID
            user_message: User message content
            message_type: Type of message ('text' or 'image')

        Returns:
            Tuple of (response_text, extracted_expense_data, budget_warning, financial_advice)
        """
        try:
            if not self.db_session:
                raise ValueError("Database session not available")

            # Get chat session
            session = (
                self.db_session.query(ChatSession).filter_by(id=session_id).first()
            )
            if not session:
                raise ValidationError(f"Chat session not found: {session_id}")

            # Save user message
            user_msg = ChatMessage(
                session_id=session_id, role="user", content=user_message
            )
            self.db_session.add(user_msg)
            self.db_session.commit()

            # Process with LangGraph agent
            result = self.langgraph_agent.run(
                user_message=user_message,
                user_id=session.user_id,
                session_id=session_id,
                message_type=message_type,
            )

            # Save AI response
            ai_msg = ChatMessage(
                session_id=session_id, role="assistant", content=result["response"]
            )
            self.db_session.add(ai_msg)
            self.db_session.commit()

            return (
                result["response"],
                result.get("extracted_expense"),
                result.get("budget_warning"),
                result.get("financial_advice"),
            )

        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            raise

    def confirm_and_save_expense(
        self,
        session_id: str,
        expense_data: Dict[str, Any],
        category_id: Optional[str] = None,
    ) -> Tuple[Expense, Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
        """
        Confirm extracted expense and save to database

        User Story 3: Includes budget warnings and financial advice when applicable

        Args:
            session_id: Chat session ID
            expense_data: Extracted expense data
            category_id: Category ID for the expense

        Returns:
            Tuple of (Saved Expense object, budget_warning, financial_advice)
        """
        try:
            if not self.db_session:
                raise ValueError("Database session not available")

            session = (
                self.db_session.query(ChatSession).filter_by(id=session_id).first()
            )
            if not session:
                raise ValidationError(f"Chat session not found: {session_id}")

            # Save expense and get budget info
            expense, budget_warning = self.expense_service.save_expense(
                user_id=session.user_id,
                expense_data=expense_data,
                category_id=category_id,
                source_type="text",
            )

            # Get financial advice if there's a budget warning (User Story 3)
            financial_advice = None
            if budget_warning:
                try:
                    logger.info(
                        f"Budget warning detected for user {session.user_id}, generating financial advice"
                    )
                    financial_advice = self.advice_service.get_financial_advice(
                        user_id=session.user_id,
                        period="monthly",
                        db_session=self.db_session,
                    )
                except Exception as advice_error:
                    logger.warning(
                        f"Failed to generate financial advice: {str(advice_error)}"
                    )
                    # Continue even if advice generation fails

            return expense, budget_warning, financial_advice

        except Exception as e:
            logger.error(f"Error confirming and saving expense: {str(e)}")
            raise

    def get_session_history(self, session_id: str) -> Tuple[ChatSession, list]:
        """
        Get chat session history

        Args:
            session_id: Chat session ID

        Returns:
            Tuple of (ChatSession, list of messages)
        """
        if not self.db_session:
            raise ValueError("Database session not available")

        session = self.db_session.query(ChatSession).filter_by(id=session_id).first()
        if not session:
            raise ValidationError(f"Chat session not found: {session_id}")

        messages = (
            self.db_session.query(ChatMessage).filter_by(session_id=session_id).all()
        )

        return session, messages

    def process_correction(
        self,
        session_id: str,
        expense_id: str,
        corrections: Dict[str, Any],
        user_id: str,
    ) -> Tuple[str, Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
        """
        Process user corrections to an expense (User Story 2)

        User Story 3: Also includes budget warnings and financial advice

        Args:
            session_id: Chat session ID
            expense_id: Expense ID to correct
            corrections: Dictionary of field corrections
            user_id: User ID

        Returns:
            Tuple of (response_text, budget_warning, financial_advice)
        """
        try:
            logger.info(
                f"Processing correction for expense {expense_id} in session {session_id}"
            )

            # Apply corrections through expense service
            updated_expense, budget_warning = self.expense_service.update_expense(
                expense_id=expense_id,
                user_id=user_id,
                corrections=corrections,
                store_learning=True,
                return_budget_warning=True,
            )

            # Store the correction interaction in chat history
            correction_message = f"Correction applied: {', '.join(corrections.keys())}"
            self._save_message(
                session_id=session_id,
                role="assistant",
                content=correction_message,
            )

            # Generate AI response acknowledging the correction
            response_parts = [
                f"Thank you! I've updated the expense with your corrections:",
            ]

            if "merchant_name" in corrections:
                response_parts.append(f"• Merchant: {corrections['merchant_name']}")
            if "amount" in corrections:
                response_parts.append(f"• Amount: ${corrections['amount']:.2f}")
            if "date" in corrections:
                response_parts.append(f"• Date: {corrections['date']}")

            response_parts.append(
                "\nI'll remember this for future similar expenses. "
                "The expense has been saved to your records."
            )

            # Get financial advice if there's a budget warning (User Story 3)
            financial_advice = None
            if budget_warning:
                response_parts.append(
                    f"\n⚠️ Budget Alert: {budget_warning.get('message', 'Budget limit exceeded')}"
                )

                # Generate financial advice
                try:
                    logger.info(
                        f"Budget warning detected for user {user_id}, generating financial advice"
                    )
                    financial_advice = self.advice_service.get_financial_advice(
                        user_id=user_id,
                        period="monthly",
                        db_session=self.db_session,
                    )

                    # Add advice to response
                    if financial_advice and financial_advice.get("advice"):
                        response_parts.append(
                            f"\n💡 Financial Advice: {financial_advice['advice']}"
                        )

                        # Add recommendations if available
                        if financial_advice.get("recommendations"):
                            response_parts.append("\nRecommendations:")
                            for rec in financial_advice["recommendations"][:3]:
                                response_parts.append(f"  • {rec}")

                except Exception as advice_error:
                    logger.warning(
                        f"Failed to generate financial advice: {str(advice_error)}"
                    )
                    # Continue even if advice generation fails

            response_text = "\n".join(response_parts)

            logger.info(f"Correction processed successfully for expense {expense_id}")

            return response_text, budget_warning, financial_advice

        except ValidationError as e:
            logger.error(f"Validation error processing correction: {str(e)}")
            return f"I couldn't apply those corrections: {str(e)}", None, None
        except Exception as e:
            logger.error(f"Error processing correction: {str(e)}")
            return (
                "I encountered an error applying your corrections. Please try again.",
                None,
                None,
            )

    def handle_correction_request(
        self,
        session_id: str,
        user_message: str,
        pending_expense_id: Optional[str] = None,
    ) -> Tuple[str, Optional[Dict[str, Any]]]:
        """
        Handle user's request to correct extracted expense information

        Args:
            session_id: Chat session ID
            user_message: User's correction message
            pending_expense_id: Optional pending expense ID to correct

        Returns:
            Tuple of (response_text, corrections_dict)
        """
        try:
            logger.info(f"Handling correction request in session {session_id}")

            # With LangGraph implementation, we can use the agent's NLP capabilities
            # to understand the correction request
            correction_prompt = f"""
            The user wants to correct an expense. Parse their message and extract the corrections.
            
            User message: "{user_message}"
            
            Extract any of these fields if mentioned:
            - merchant_name (location/restaurant name)
            - amount (price/cost)
            - date (when the expense occurred)
            
            Return ONLY a JSON object with the corrections, like:
            {{"merchant_name": "Corrected Name", "amount": 25.50, "date": "2025-10-16"}}
            
            If you cannot extract corrections, return: {{"error": "Could not understand corrections"}}
            """

            # Use the LangGraph agent to process this request
            if self.langgraph_agent:
                from langchain_core.messages import HumanMessage
                from langchain_google_genai import ChatGoogleGenerativeAI

                # Initialize a temporary model for this specific task
                temp_model = ChatGoogleGenerativeAI(
                    model="gemini-2.5-flash", temperature=0.1
                )

                response = temp_model.invoke([HumanMessage(content=correction_prompt)])

                # Parse the response
                import re

                response_text = response.content.strip()

                # Clean up markdown if present
                if "```json" in response_text:
                    response_text = (
                        response_text.split("```json")[1].split("```")[0].strip()
                    )
                elif "```" in response_text:
                    response_text = (
                        response_text.split("```")[1].split("```")[0].strip()
                    )

                corrections = json.loads(response_text)

                if "error" in corrections:
                    return (
                        "I'm not sure what you'd like to correct. Could you please specify "
                        "which fields you want to change (merchant name, amount, or date)?",
                        None,
                    )

                # Format confirmation message
                response_parts = ["I understand you want to make these corrections:"]
                if "merchant_name" in corrections:
                    response_parts.append(f"• Merchant: {corrections['merchant_name']}")
                if "amount" in corrections:
                    response_parts.append(f"• Amount: ${corrections['amount']:.2f}")
                if "date" in corrections:
                    response_parts.append(f"• Date: {corrections['date']}")

                response_parts.append("\nShould I apply these corrections?")

                return "\n".join(response_parts), corrections
            else:
                # Fallback if langgraph agent is not available
                return (
                    "I had trouble understanding your corrections. Please be specific about what needs to be changed.",
                    None,
                )

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI correction response: {str(e)}")
            return (
                "I had trouble understanding your corrections. Could you please rephrase?",
                None,
            )
        except Exception as e:
            logger.error(f"Error handling correction request: {str(e)}")
            return (
                "I encountered an error processing your request. Please try again.",
                None,
            )

    def close_session(self, session_id: str) -> ChatSession:
        """
        Close a chat session

        Args:
            session_id: Chat session ID

        Returns:
            Updated ChatSession object
        """
        if not self.db_session:
            raise ValueError("Database session not available")

        session = self.db_session.query(ChatSession).filter_by(id=session_id).first()
        if not session:
            raise ValidationError(f"Chat session not found: {session_id}")

        session.status = "completed"
        self.db_session.commit()
        self.db_session.refresh(session)

        logger.info(f"Chat session closed: {session_id}")
        return session

    def _save_message(self, session_id: str, role: str, content: str) -> None:
        """
        Save a message to chat history

        Args:
            session_id: Chat session ID
            role: Message role (user/assistant)
            content: Message content
        """
        try:
            if not self.db_session:
                return

            message = ChatMessage(session_id=session_id, role=role, content=content)
            self.db_session.add(message)
            self.db_session.commit()
        except Exception as e:
            logger.error(f"Error saving message: {str(e)}")
