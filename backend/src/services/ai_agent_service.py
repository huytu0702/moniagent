"""
AI Agent Service using LangGraph for managing expense tracking conversations
"""

import logging
import json
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
from sqlalchemy.orm import Session

# Use google-generativeai directly instead of langchain-google-genai
import google.generativeai as genai

from src.services.expense_processing_service import ExpenseProcessingService
from src.services.budget_management_service import BudgetManagementService
from src.services.financial_advice_service import FinancialAdviceService
from src.models.expense import Expense
from src.models.chat_session import ChatSession, ChatMessage
from src.utils.exceptions import ValidationError
import os

logger = logging.getLogger(__name__)


class AIAgentService:
    """
    Service for managing AI-powered expense tracking conversations
    """

    def __init__(self, db_session: Optional[Session] = None):
        self.db_session = db_session
        self.expense_service = ExpenseProcessingService(db_session)
        self.budget_service = BudgetManagementService(db_session)
        self.advice_service = FinancialAdviceService()

        # Initialize Google Generative AI
        api_key = os.getenv("GOOGLE_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("gemini-2.5-flash-lite")

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
    ) -> Tuple[str, Optional[Dict[str, Any]], Optional[Dict[str, Any]], Optional[str]]:
        """
        Process a user message and generate a response

        Args:
            session_id: Chat session ID
            user_message: User message content
            message_type: Type of message ('text' or 'image')

        Returns:
            Tuple of (response_text, extracted_expense_data, budget_warning, advice)
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

            # Extract expense information
            extracted_expense = None
            budget_warning = None
            advice = None

            if message_type == "text":
                extracted_expense = self._extract_from_text(user_message)
            elif message_type == "image":
                extracted_expense = self._extract_from_image(user_message)

            # Generate AI response
            if message_type == "image" and not extracted_expense:
                response_text = (
                    "I couldn't read the image. Please upload a clear receipt "
                    "photo in JPG or PNG format, showing amount and merchant."
                )
            else:
                response_text = self._generate_response(user_message, extracted_expense)

            # Save AI response
            ai_msg = ChatMessage(
                session_id=session_id, role="assistant", content=response_text
            )
            self.db_session.add(ai_msg)
            self.db_session.commit()

            # If expense was extracted and valid, provide budget info and advice
            if extracted_expense and self.expense_service.validate_extracted_expense(
                extracted_expense
            ):
                # For now, we'll return the extracted info for user confirmation
                pass

            return response_text, extracted_expense, budget_warning, advice

        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            raise

    def _extract_from_text(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Extract expense from text using AI

        Args:
            text: Text content

        Returns:
            Extracted expense data or None
        """
        try:
            # Phase 6 optimization: try lightweight parser first
            try:
                fast_data = self.expense_service.extract_expense_from_text(text)
                if fast_data and (fast_data.get("amount") or fast_data.get("merchant_name")):
                    return fast_data
            except Exception as fast_err:
                logger.debug(
                    f"Lightweight text extraction fallback due to: {fast_err}"
                )

            extraction_prompt = f"""Extract expense information from the following text. Return ONLY valid JSON.
                
Text: {text}

Return JSON with these fields (use null for missing data):
{{
    "merchant_name": "string or null",
    "amount": number or null,
    "date": "YYYY-MM-DD or null",
    "confidence": 0-1,
    "description": "string or null"
}}
"""

            response = self.model.generate_content(extraction_prompt)
            response_text = response.text.strip()

            # Clean up markdown if present
            if "```json" in response_text:
                response_text = (
                    response_text.split("```json")[1].split("```")[0].strip()
                )
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()

            extracted_data = json.loads(response_text)
            return extracted_data

        except Exception as e:
            logger.warning(f"Failed to extract expense from text: {str(e)}")
            return None

    def _extract_from_image(self, image_path: str) -> Optional[Dict[str, Any]]:
        """
        Extract expense from image using OCR

        Args:
            image_path: Path to image file

        Returns:
            Extracted expense data or None
        """
        try:
            if not image_path or not os.path.exists(image_path):
                logger.warning(f"Image file not found: {image_path}")
                return None
            with open(image_path, "rb") as f:
                return self.expense_service.extract_expense_from_image(f)
        except Exception as e:
            logger.warning(f"Failed to extract expense from image: {str(e)}")
            return None

    def _generate_response(
        self, user_message: str, extracted_expense: Optional[Dict[str, Any]]
    ) -> str:
        """
        Generate AI response using LLM

        Args:
            user_message: User message
            extracted_expense: Extracted expense data if available

        Returns:
            AI response text
        """
        try:
            if extracted_expense:
                # Format extracted data for confirmation
                amounts = extracted_expense.get("amounts")
                if amounts and isinstance(amounts, list) and len(amounts) > 1:
                    expense_text = (
                        f"I found multiple amounts {amounts} in your message. "
                        f"Please confirm which amount to record, or split into separate expenses."
                    )
                else:
                    expense_text = (
                        f"I found the following expense information:\n"
                        f"- Merchant: {extracted_expense.get('merchant_name', 'Unknown')}\n"
                        f"- Amount: ${extracted_expense.get('amount', 0):.2f}\n"
                        f"- Date: {extracted_expense.get('date', 'Not specified')}\n"
                        f"- Confidence: {extracted_expense.get('confidence', 0)*100:.0f}%\n\n"
                        f"Is this correct? Please confirm or provide corrections."
                    )
                return expense_text
            else:
                # Generic response when no expense extracted: provide explicit guidance
                return (
                    "I couldn't extract expense details. Please include: amount (e.g., $12.50), "
                    "merchant (e.g., Starbucks), and optional date (YYYY-MM-DD)."
                )

        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return "I had trouble understanding that. Could you please rephrase your expense?"

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

            # Use AI to parse the correction from user message
            prompt = f"""
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

            response = self.model.generate_content(prompt)
            response_text = response.text.strip()

            # Parse the JSON response
            # Remove markdown code blocks if present
            if "```json" in response_text:
                response_text = (
                    response_text.split("```json")[1].split("```")[0].strip()
                )
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()

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
