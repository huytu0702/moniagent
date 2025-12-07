"""
LangGraph implementation for the AI financial assistant
"""

from typing import Dict, List, TypedDict, Annotated, Union, Optional, Any
import operator
import json
import logging
import re
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import interrupt, Command
from langchain_core.tools import tool
from src.services.expense_processing_service import ExpenseProcessingService
from src.services.budget_management_service import BudgetManagementService
from src.services.financial_advice_service import FinancialAdviceService
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class AgentState(TypedDict):
    """State for the AI financial agent

    NOTE: Do NOT include non-serializable objects like db_session here.
    LangGraph checkpointer needs to serialize the entire state.
    Use self.db_session in the LangGraphAIAgent class instead.
    """

    messages: Annotated[List[BaseMessage], operator.add]
    user_id: str
    session_id: str
    message_type: str

    # Expense extraction
    extracted_expense: Dict
    saved_expense: Dict
    original_category_id: str  # Track original category for learning

    # Confirmation flow
    asking_confirmation: bool
    awaiting_user_response: bool
    user_confirmation_response: str  # User's response after interrupt

    # Update flow
    wants_update: bool  # Whether user wants to update expense
    corrections: Dict  # Corrections to apply

    # Budget & Advice
    budget_warning: Dict
    financial_advice: Dict


class ExpenseExtractionTool(BaseModel):
    """Tool for extracting expense information from user input"""

    user_message: str = Field(description="The user message to extract expense from")
    message_type: str = Field(
        default="text", description="Type of message: text or image"
    )


class ExpenseConfirmationTool(BaseModel):
    """Tool for confirming and saving expenses"""

    expense_data: Dict = Field(description="Expense data to confirm and save")
    category_id: str = Field(default=None, description="Category ID for the expense")


class BudgetCheckTool(BaseModel):
    """Tool for checking budget status after expense is added"""

    user_id: str = Field(description="User ID to check budget for")
    expense_amount: float = Field(
        description="Amount of the expense to check against budget"
    )


class FinancialAdviceTool(BaseModel):
    """Tool for generating financial advice"""

    user_id: str = Field(description="User ID to generate advice for")
    period: str = Field(
        default="monthly", description="Time period for advice: daily, weekly, monthly"
    )


class LangGraphAIAgent:
    """AI Financial Assistant using LangGraph framework"""

    def __init__(self, db_session: Session, checkpointer=None):
        self.db_session = db_session
        self.expense_service = ExpenseProcessingService(db_session)
        self.budget_service = BudgetManagementService(db_session)
        self.advice_service = FinancialAdviceService()

        # Initialize checkpointer for state persistence
        self.checkpointer = checkpointer or InMemorySaver()

        # Temporary storage for image files (not serializable in state)
        # Key: session_id, Value: image_file BytesIO
        self._image_files: Dict[str, Any] = {}

        # Initialize LLM - use gemini-2.5-flash-lite for lightweight operations
        self.model = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.1)
        self.lite_model = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash-lite", temperature=0.1
        )

        # Bind tools to the model
        self.model_with_tools = self.model.bind_tools(
            [
                ExpenseExtractionTool,
                ExpenseConfirmationTool,
                BudgetCheckTool,
                FinancialAdviceTool,
            ]
        )

        # Build graph with checkpointer
        self.graph = self._build_graph()

    def _extract_expense(self, state: AgentState) -> Dict:
        """Extract expense from user message using the service"""
        messages = state.get("messages", [])
        if not messages or len(messages) == 0:
            logger.warning("No messages in state for expense extraction")

        user_message = messages[-1].content if messages else ""
        message_type = state.get("message_type", "text")
        user_id = state.get("user_id")
        session_id = state.get("session_id")

        # Get image_file from temporary storage (not serializable in state)
        image_file = self._image_files.get(session_id) if session_id else None

        extracted_expense = None
        if message_type == "text":
            extracted_expense = self.expense_service.extract_expense_from_text(
                user_message, user_id=user_id
            )
        elif message_type == "image":
            # Use image_file if available, otherwise fallback to user_message as path
            if image_file:
                # Reset file pointer before processing
                image_file.seek(0)
                extracted_expense = self.expense_service.extract_expense_from_image(
                    image_file, user_id=user_id  # Pass user_id for auto-categorization
                )
                # Clear from temporary storage after use
                if session_id in self._image_files:
                    del self._image_files[session_id]
            else:
                # Fallback: assume user_message contains image path
                logger.warning("No image_file provided, using user_message as path")
                extracted_expense = self.expense_service.extract_expense_from_image(
                    user_message,
                    user_id=user_id,  # Pass user_id for auto-categorization
                )

        return {"extracted_expense": extracted_expense}

    def _prepare_expense_for_confirmation(self, state: AgentState) -> Dict:
        """Prepare extracted expense for user confirmation (NO SAVE YET)"""
        expense_data = state.get("extracted_expense", {})

        if expense_data:
            # Get category name if category_id exists
            category_name = None
            category_id = expense_data.get("category_id")
            if category_id and self.db_session:
                from src.models.category import Category

                category = (
                    self.db_session.query(Category).filter_by(id=category_id).first()
                )
                if category:
                    category_name = category.name

            # Handle date - default to today if not provided
            from datetime import datetime
            expense_date = expense_data.get("date")
            
            if expense_date:
                # Already has a date string - convert to friendly format
                try:
                    dt = datetime.fromisoformat(expense_date)
                    display_date = dt.strftime("%d/%m/%Y")  # 07/12/2025
                except (ValueError, TypeError):
                    display_date = expense_date
            else:
                # Set actual date for saving and display
                now = datetime.utcnow()
                expense_data["date"] = now.strftime("%Y-%m-%d")  # For saving
                display_date = now.strftime("%d/%m/%Y")  # For display: 07/12/2025

            # Prepare pending expense (NOT saved yet)
            pending_expense = {
                "id": None,  # No ID yet - not saved
                "merchant_name": expense_data.get("merchant_name") or "Không xác định",
                "amount": expense_data.get("amount"),
                "date": display_date,  # Display friendly text
                "actual_date": expense_data.get("date"),  # Actual date for saving
                "category_id": category_id,
                "category_name": category_name or "Chưa phân loại",
            }

            return {
                "extracted_expense": expense_data,
                "saved_expense": pending_expense,  # Using same field but not saved yet
                "original_category_id": category_id,  # Track for learning
                "asking_confirmation": True,
                "awaiting_user_response": True,
            }

        return {}

    def _ask_confirmation(self, state: AgentState) -> Dict:
        """Ask user to confirm expense before saving - PAUSE HERE with interrupt()"""
        saved_expense = state.get("saved_expense", {})

        if not saved_expense:
            return {
                "messages": [
                    AIMessage(
                        content="Không có thông tin chi tiêu để xác nhận. Bạn có thể nhập lại không?"
                    )
                ],
                "asking_confirmation": False,
            }

        # Format the pending expense information
        category_display = (
            saved_expense.get('category_name')
            or saved_expense.get('category_id')
            or 'Chưa phân loại'
        )
        expense_summary = f"""Tôi đã trích xuất được thông tin chi tiêu sau:

📌 **Thông tin chi tiêu:**
   • Cửa hàng: {saved_expense.get('merchant_name', 'Không xác định')}
   • Số tiền: {saved_expense.get('amount', 0):,.0f}đ
   • Ngày: {saved_expense.get('date', 'Hôm nay')}
   • Danh mục: {category_display}

Bạn xác nhận thông tin trên đúng không? (Nhắn "ok" để lưu, hoặc cho tôi biết cần sửa gì)"""

        # Create confirmation payload for interrupt
        confirmation_payload = {
            "type": "expense_confirmation",
            "saved_expense": saved_expense,
            "message": expense_summary.strip(),
        }

        # INTERRUPT - Wait for user response
        # This pauses the graph execution until user responds via Command(resume=...)
        user_response = interrupt(confirmation_payload)

        # This code runs AFTER user responds via Command(resume=...)
        # Convert user_response to string if needed
        user_response_str = (
            user_response if isinstance(user_response, str) else str(user_response)
        )

        # Store user response in state and add to messages
        return {
            "messages": [
                AIMessage(content=expense_summary.strip()),
                HumanMessage(content=user_response_str),
            ],
            "user_confirmation_response": user_response_str,
            "asking_confirmation": False,
            "awaiting_user_response": False,
        }

    def _detect_update_intent(self, state: AgentState) -> Dict:
        """Detect if user wants to update the expense using lite model"""
        # Get user response from confirmation (set by interrupt resume) or from latest message
        user_message = state.get("user_confirmation_response", "")

        # If no confirmation response, try to get from messages (check for non-empty list)
        messages = state.get("messages", [])
        if not user_message and messages and len(messages) > 0:
            user_message = messages[-1].content

        try:
            # Get current expense info for context
            saved_expense = state.get("saved_expense", {})
            expense_context = ""
            if saved_expense:
                expense_context = f"""
Thông tin chi tiêu hiện tại:
- Cửa hàng: {saved_expense.get('merchant_name', 'Không xác định')}
- Số tiền: {saved_expense.get('amount', 0):,.0f}đ
- Ngày: {saved_expense.get('date', 'Hôm nay')}
- Danh mục: {saved_expense.get('category_name', 'Chưa phân loại')}
"""

            intent_prompt = f"""Phân tích ý định của người dùng:

Người dùng vừa được hỏi xác nhận thông tin chi tiêu (CHƯA LƯU vào hệ thống).
{expense_context}
Bây giờ người dùng trả lời: "{user_message}"

Hãy xác định:
1. Người dùng có muốn chỉnh sửa thông tin không? (yes/no)
   - Nếu người dùng nói "ok", "đúng", "đúng rồi", "lưu", "xác nhận" → wants_update = false
   - Nếu người dùng đề cập đến việc sửa/thay đổi bất kỳ trường nào → wants_update = true
   
2. Nếu có muốn sửa (wants_update = true), hãy trích xuất TẤT CẢ những thay đổi mà người dùng muốn:
   - merchant_name: (tên cửa hàng mới nếu có, để null nếu không đề cập)
   - amount: (số tiền mới nếu có, để null nếu không đề cập)
   - date: (ngày mới nếu có, để null nếu không đề cập)
   - category_name: (tên danh mục mới nếu có, để null nếu không đề cập)
   
   QUAN TRỌNG: Người dùng có thể yêu cầu sửa NHIỀU trường cùng lúc!
   Ví dụ: "sửa cửa hàng thành starbucks và ngày thành 25/11/2025" → cần trích xuất CẢ HAI

QUAN TRỌNG về date:
- Người dùng có thể nhập ngày theo nhiều định dạng: DD/MM/YYYY, DD-MM-YYYY, ngày/tháng/năm, v.v.
- Ví dụ: "26/11/2025", "26-11-2025", "ngày 26 tháng 11 năm 2025", "25/11/2025"
- Bạn PHẢI chuyển đổi sang định dạng YYYY-MM-DD
- Ví dụ: "26/11/2025" -> "2025-11-26", "25/11/2025" -> "2025-11-25"
- Nếu không có năm, mặc định là năm 2025

Ví dụ phân tích:
- "sửa cửa hàng thành starbucks và ngày thành 25/11/2025" → wants_update: true, corrections: {{"merchant_name": "starbucks", "date": "2025-11-25"}}
- "đổi danh mục sang ăn uống" → wants_update: true, corrections: {{"category_name": "Ăn uống"}}
- "ok" → wants_update: false, corrections: {{}}
- "sửa ngày thành 26/11/2025" → wants_update: true, corrections: {{"date": "2025-11-26"}}
   
Trả về JSON format:
{{
  "wants_update": true/false,
  "corrections": {{
    "merchant_name": "..." hoặc null,
    "amount": 123.45 hoặc null,
    "date": "YYYY-MM-DD" hoặc null,
    "category_name": "..." hoặc null
  }},
  "reason": "Giải thích tại sao"
}}

Chỉ trả về JSON, không có markdown."""

            response = self.lite_model.invoke([HumanMessage(content=intent_prompt)])
            response_text = response.content.strip()

            logger.info(f"Intent detection response: {response_text}")

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

                intent_data = json.loads(response_text)

                # Filter out null/None values from corrections
                raw_corrections = intent_data.get("corrections", {})
                corrections = {
                    k: v
                    for k, v in raw_corrections.items()
                    if v is not None and v != "null" and v != ""
                }

                # Additional date format conversion if needed
                if "date" in corrections:
                    corrections["date"] = self._normalize_date_format(
                        corrections["date"]
                    )

                return {
                    "wants_update": intent_data.get("wants_update", False),
                    "corrections": corrections,
                }
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse intent response: {str(e)}")
                logger.error(f"Response text was: {response_text}")
                # Fallback: check for keywords and try to extract basic info
                user_lower = user_message.lower()
                keywords_update = [
                    "thay",
                    "sửa",
                    "đổi",
                    "chỉnh",
                    "lại",
                    "khác",
                    "sai",
                    "thành",
                ]
                wants_update = any(kw in user_lower for kw in keywords_update)

                # Try to extract basic corrections from text
                corrections = {}
                if wants_update:
                    import re

                    user_lower = user_message.lower()

                    # Try to extract merchant name - look for patterns like:
                    # "sửa cửa hàng thành starbucks"
                    # "cửa hàng thành starbucks"
                    merchant_patterns = [
                        r'(?:sửa|thay|đổi)\s+(?:cửa\s+hàng|merchant|store).*?thành\s+([^\s]+(?:\s+[^\s]+)*?)(?:\s+và|\s+ngày|\s+amount|$|\.)',
                        r'cửa\s+hàng.*?thành\s+([^\s]+(?:\s+[^\s]+)*?)(?:\s+và|\s+ngày|\s+amount|$|\.)',
                    ]
                    for pattern in merchant_patterns:
                        merchant_match = re.search(pattern, user_message, re.IGNORECASE)
                        if merchant_match:
                            merchant_name = merchant_match.group(1).strip()
                            # Remove common words that might be attached
                            merchant_name = re.sub(
                                r'\s+(và|and|,)\s*$',
                                '',
                                merchant_name,
                                flags=re.IGNORECASE,
                            )
                            if merchant_name and len(merchant_name) > 1:
                                corrections["merchant_name"] = merchant_name
                                break

                    # Try to extract date - look for patterns like:
                    # "ngày thành 25/11/2025"
                    # "sửa ngày thành 25/11/2025"
                    date_patterns = [
                        r'(?:sửa|thay|đổi)\s+ngày.*?thành\s+(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})',
                        r'ngày.*?thành\s+(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})',
                        r'(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})',  # Any date format
                        r'ngày\s+(\d{1,2})\s+tháng\s+(\d{1,2})\s+năm\s+(\d{4})',  # ngày DD tháng MM năm YYYY
                    ]
                    for pattern in date_patterns:
                        date_match = re.search(pattern, user_message, re.IGNORECASE)
                        if date_match:
                            if (
                                len(date_match.groups()) == 3
                            ):  # ngày DD tháng MM năm YYYY
                                day, month, year = date_match.groups()
                                corrections["date"] = (
                                    f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                                )
                            else:  # DD/MM/YYYY format
                                date_str = date_match.group(1)
                                normalized = self._normalize_date_format(date_str)
                                if normalized:
                                    corrections["date"] = normalized
                            break

                    # Try to extract amount
                    amount_patterns = [
                        r'(?:sửa|thay|đổi)\s+(?:số\s+tiền|amount).*?thành\s+(\d+(?:[,\.]\d{3})*)\s*(?:k|K|đ|vnd)?',
                        r'số\s+tiền.*?thành\s+(\d+(?:[,\.]\d{3})*)\s*(?:k|K|đ|vnd)?',
                        r'(\d+(?:[,\.]\d{3})*)\s*(?:k|K|đ|vnd)',  # Any amount format
                    ]
                    for pattern in amount_patterns:
                        amount_match = re.search(pattern, user_message, re.IGNORECASE)
                        if amount_match:
                            amount_str = (
                                amount_match.group(1).replace(",", "").replace(".", "")
                            )
                            try:
                                amount = float(amount_str)
                                # Check if "k" is in the matched portion
                                matched_text = amount_match.group(0).lower()
                                if "k" in matched_text:
                                    amount *= 1000
                                corrections["amount"] = amount
                                break
                            except ValueError:
                                pass

                    # Try to extract category
                    category_patterns = [
                        r'(?:sửa|thay|đổi|chuyển)\s+(?:danh\s+mục|loại|nhóm).*?thành\s+([^\s]+(?:\s+[^\s]+)*?)(?:\s+và|\s+ngày|\s+amount|\s+cửa\s+hàng|$|\.)',
                        r'(?:danh\s+mục|loại|nhóm).*?thành\s+([^\s]+(?:\s+[^\s]+)*?)(?:\s+và|\s+ngày|\s+amount|\s+cửa\s+hàng|$|\.)',
                    ]
                    for pattern in category_patterns:
                        cat_match = re.search(pattern, user_message, re.IGNORECASE)
                        if cat_match:
                            category_name = cat_match.group(1).strip()
                            # Remove common words
                            category_name = re.sub(r'\s+(và|and|,)\s*$', '', category_name, flags=re.IGNORECASE)
                            if category_name and len(category_name) > 1:
                                corrections["category_name"] = category_name
                                break

                logger.warning(
                    f"Using fallback extraction. wants_update: {wants_update}, corrections: {corrections}"
                )
                return {"wants_update": wants_update, "corrections": corrections}

        except Exception as e:
            logger.error(f"Error detecting update intent: {str(e)}")
            return {"wants_update": False, "corrections": {}}

    def _resolve_category(self, category_name: str, user_id: str) -> tuple[Optional[str], Optional[str]]:
        """Resolve category name to ID"""
        if not category_name or not user_id or not self.db_session:
            return None, None
            
        from src.models.category import Category
        from sqlalchemy import func
        
        # 1. Try exact match
        category = self.db_session.query(Category).filter(
            Category.user_id == user_id,
            func.lower(Category.name) == category_name.lower()
        ).first()
        
        if category:
            return str(category.id), category.name
            
        # 2. Try partial match
        categories = self.db_session.query(Category).filter(
            Category.user_id == user_id
        ).all()
        
        # Simple fuzzy match
        best_match = None
        best_score = 0
        
        category_name_lower = category_name.lower()
        
        for cat in categories:
            cat_name_lower = cat.name.lower()
            if category_name_lower in cat_name_lower or cat_name_lower in category_name_lower:
                # Prefer the one that is contained in the other
                score = len(category_name_lower) / len(cat_name_lower) if len(cat_name_lower) > len(category_name_lower) else len(cat_name_lower) / len(category_name_lower)
                if score > best_score:
                    best_score = score
                    best_match = cat
                    
        if best_match and best_score > 0.5:
            return str(best_match.id), best_match.name
            
        return None, None

    def _process_update(self, state: AgentState) -> Dict:
        """Process corrections to pending expense (NOT saved yet) - returns to ask_confirmation"""
        saved_expense = state.get("saved_expense", {})
        corrections = state.get("corrections", {})

        if not saved_expense or not corrections:
            return {
                "messages": [
                    AIMessage(
                        content="Tôi không hiểu những thay đổi bạn muốn thực hiện. Có thể hãy nói rõ hơn nhé?"
                    )
                ]
            }

        # Update pending expense with corrections (NO DB save yet)
        # Handle date display format
        from datetime import datetime
        raw_date = corrections.get("date", saved_expense.get("date"))
        display_date = raw_date
        
        if raw_date:
            try:
                # Try to parse and format to DD/MM/YYYY
                dt = datetime.fromisoformat(raw_date)
                display_date = dt.strftime("%d/%m/%Y")
            except (ValueError, TypeError):
                # Keep as-is if already formatted or invalid
                display_date = raw_date
        else:
            # Default to today
            now = datetime.utcnow()
            display_date = now.strftime("%d/%m/%Y")

        updated_pending_expense = {
            "id": None,  # Still not saved
            "merchant_name": corrections.get(
                "merchant_name", saved_expense.get("merchant_name")
            )
            or "Không xác định",
            "amount": corrections.get("amount", saved_expense.get("amount")),
            "date": display_date,
            "category_id": saved_expense.get("category_id"),
            "category_name": saved_expense.get("category_name") or "Chưa phân loại",
        }

        # Handle category update specifically
        if "category_name" in corrections:
            user_id = state.get("user_id")
            new_cat_id, new_cat_name = self._resolve_category(corrections["category_name"], user_id)
            if new_cat_id:
                updated_pending_expense["category_id"] = new_cat_id
                updated_pending_expense["category_name"] = new_cat_name
                # Also update corrections to reflect the resolved name
                corrections["category_name"] = new_cat_name
            else:
                # Could not resolve category - keep as is but maybe warn user?
                # For now just keep the text the user provided as a hint, but don't change ID
                # Or maybe we shouldn't change anything if we can't resolve it
                pass

        # Also update extracted_expense for when we save
        updated_extracted = state.get("extracted_expense", {}).copy()
        if "merchant_name" in corrections:
            updated_extracted["merchant_name"] = corrections["merchant_name"]
        if "amount" in corrections:
            updated_extracted["amount"] = corrections["amount"]
        if "date" in corrections:
            updated_extracted["date"] = corrections["date"]
        if "category_name" in corrections and updated_pending_expense.get("category_id"):
             updated_extracted["category_id"] = updated_pending_expense["category_id"]

        logger.info(f"Expense corrections applied (pending): {corrections}")

        # Build confirmation message with updated info
        category_display = (
            updated_pending_expense.get("category_name") or "Chưa phân loại"
        )
        response_message = f"""Tôi đã cập nhật thông tin chi tiêu:

📌 **Thông tin chi tiêu (đã sửa):**
   • Cửa hàng: {updated_pending_expense.get('merchant_name', 'Không xác định')}
   • Số tiền: {updated_pending_expense.get('amount', 0):,.0f}đ
   • Ngày: {updated_pending_expense.get('date', 'Hôm nay')}
   • Danh mục: {category_display}

Bạn xác nhận thông tin trên đúng không? (Nhắn "ok" để lưu, hoặc cho tôi biết cần sửa gì)"""

        return {
            "messages": [AIMessage(content=response_message.strip())],
            "saved_expense": updated_pending_expense,
            "extracted_expense": updated_extracted,
            "corrections": {},  # Clear corrections for next round
            "wants_update": False,
            "asking_confirmation": True,
        }

    def _save_expense(self, state: AgentState) -> Dict:
        """Actually save the expense to database after user confirmation"""
        expense_data = state.get("extracted_expense", {})
        user_id = state["user_id"]
        saved_expense = state.get("saved_expense", {})
        original_category_id = state.get("original_category_id")

        if not expense_data:
            return {
                "messages": [AIMessage(content="Không có thông tin chi tiêu để lưu.")]
            }

        try:
            # Now actually save to database
            expense, budget_warning = self.expense_service.save_expense(
                user_id=user_id,
                expense_data=expense_data,
                category_id=expense_data.get("category_id"),
                source_type="text",
            )

            # Check if category was changed/added by user - trigger learning
            # Learn if: 
            # 1. User changed category (original != final)
            # 2. User added category when there was none (original is None, final exists)
            final_category_id = expense_data.get("category_id") or saved_expense.get("category_id")
            category_was_changed = (
                final_category_id is not None 
                and (
                    original_category_id is None  # User added category
                    or str(original_category_id) != str(final_category_id)  # User changed category
                )
            )

            learning_message = ""
            if category_was_changed:
                try:
                    from src.services.category_learning_service import CategoryLearningService
                    
                    learning_service = CategoryLearningService(self.db_session)
                    learning_result = learning_service.learn_from_correction(
                        user_id=user_id,
                        expense_id=str(expense.id),
                        corrected_category_id=str(final_category_id),
                        original_category_id=str(original_category_id) if original_category_id else None,
                    )
                    
                    if learning_result and learning_result.get("keywords_learned"):
                        keywords = learning_result.get("keywords_learned", [])
                        logger.info(
                            f"Learned from category correction: {keywords} -> {saved_expense.get('category_name')}"
                        )
                        learning_message = "\n📚 Tôi đã ghi nhớ để lần sau phân loại chính xác hơn!"
                except Exception as learning_error:
                    logger.warning(f"Category learning failed (non-blocking): {str(learning_error)}")

            # Build confirmation message
            response_parts = ["✅ Đã lưu chi tiêu vào hệ thống:"]
            response_parts.append(
                f"   • Cửa hàng: {saved_expense.get('merchant_name', 'Không xác định')}"
            )
            response_parts.append(
                f"   • Số tiền: {saved_expense.get('amount', 0):,.0f}đ"
            )
            response_parts.append(f"   • Ngày: {saved_expense.get('date', 'Hôm nay')}")
            response_parts.append(
                f"   • Danh mục: {saved_expense.get('category_name', 'Chưa phân loại')}"
            )

            # Add learning message if category was changed
            if learning_message:
                response_parts.append(learning_message)

            # Add budget warning if applicable
            if budget_warning:
                response_parts.append(
                    f"\n⚠️ {budget_warning.get('message', 'Cảnh báo ngân sách')}"
                )

            response_text = "\n".join(response_parts)

            logger.info(f"Expense saved to database: {expense.id}")

            # Update saved_expense with actual ID
            final_saved_expense = {
                "id": str(expense.id),
                "merchant_name": saved_expense.get("merchant_name"),
                "amount": saved_expense.get("amount"),
                "date": saved_expense.get("date"),
                "category_id": saved_expense.get("category_id"),
                "category_name": saved_expense.get("category_name"),
            }

            return {
                "messages": [AIMessage(content=response_text)],
                "budget_warning": budget_warning,
                "saved_expense": final_saved_expense,
                "asking_confirmation": False,
            }

        except Exception as e:
            logger.error(f"Error saving expense: {str(e)}")
            return {
                "messages": [
                    AIMessage(
                        content=f"Xin lỗi, tôi gặp lỗi khi lưu chi tiêu: {str(e)}"
                    )
                ]
            }

    def _generate_financial_advice(self, state: AgentState) -> Dict:
        """Generate financial advice based on user's spending"""
        user_id = state["user_id"]

        advice = self.advice_service.get_financial_advice(
            user_id=user_id, period="monthly", db_session=self.db_session
        )

        return {"financial_advice": advice}

    def _call_model(self, state: AgentState) -> Dict:
        """Call the LLM model with current state"""
        messages = state.get("messages", [])

        # If no messages, create a default context
        if not messages:
            # Build context from state
            user_response = state.get("user_confirmation_response", "")
            saved_expense = state.get("saved_expense", {})
            wants_update = state.get("wants_update", False)
            corrections = state.get("corrections", {})

            # Create a summary message
            if saved_expense and user_response:
                if wants_update and not corrections:
                    context = f"Người dùng muốn chỉnh sửa chi tiêu nhưng chưa nêu rõ chi tiết. Chi tiêu hiện tại: {saved_expense.get('merchant_name')} - {saved_expense.get('amount')}đ. Hãy hỏi họ muốn thay đổi gì."
                elif wants_update and corrections:
                    context = f"Đã cập nhật chi tiêu với các thay đổi: {corrections}. Hãy xác nhận với người dùng."
                else:
                    context = f"Chi tiêu đã được lưu: {saved_expense.get('merchant_name')} - {saved_expense.get('amount')}đ. Hỏi người dùng có cần gì thêm không."
                messages = [HumanMessage(content=context)]
            else:
                messages = [
                    HumanMessage(content="Xin chào, tôi có thể giúp gì cho bạn?")
                ]

        try:
            response = self.model_with_tools.invoke(messages)
            return {"messages": [response]}
        except Exception as e:
            logger.error(f"Error calling model: {str(e)}")
            return {
                "messages": [
                    AIMessage(
                        content="Xin lỗi, tôi gặp lỗi khi xử lý. Vui lòng thử lại."
                    )
                ]
            }

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow"""
        workflow = StateGraph(AgentState)

        # Add nodes
        workflow.add_node("extract_expense", self._extract_expense)
        workflow.add_node(
            "prepare_confirmation", self._prepare_expense_for_confirmation
        )
        workflow.add_node("ask_confirmation", self._ask_confirmation)  # Has interrupt()
        workflow.add_node("detect_update_intent", self._detect_update_intent)
        workflow.add_node("process_update", self._process_update)
        workflow.add_node(
            "save_expense", self._save_expense
        )  # NEW: Actually saves to DB
        workflow.add_node("generate_advice", self._generate_financial_advice)
        workflow.add_node("llm_call", self._call_model)

        # Set entry point
        workflow.set_entry_point("extract_expense")

        # Add conditional edges based on tool calls
        workflow.add_conditional_edges(
            "extract_expense",
            self._route_after_extraction,
            {"prepare_confirmation": "prepare_confirmation", "llm_call": "llm_call"},
        )

        # After preparing expense, go to ask_confirmation (no save yet)
        workflow.add_edge("prepare_confirmation", "ask_confirmation")

        # AFTER interrupt resumes → route based on user response
        workflow.add_conditional_edges(
            "ask_confirmation",
            self._route_after_user_response,
            {
                "detect_update_intent": "detect_update_intent",
                "save_expense": "save_expense",  # User confirmed → save
            },
        )

        # Route after detecting intent
        workflow.add_conditional_edges(
            "detect_update_intent",
            self._route_after_intent,
            {
                "process_update": "process_update",
                "save_expense": "save_expense",  # If no clear update, save anyway
                "llm_call": "llm_call",  # Fallback for unclear cases
            },
        )

        # After update, go back to ask_confirmation for re-confirmation
        workflow.add_conditional_edges(
            "process_update",
            self._route_after_update,
            {"ask_confirmation": "ask_confirmation"},
        )

        # After saving, check budget and generate advice if needed
        workflow.add_conditional_edges(
            "save_expense",
            self._route_after_save,
            {"generate_advice": "generate_advice", "end": END},
        )

        workflow.add_edge("generate_advice", END)

        workflow.add_edge("llm_call", END)

        # Compile with checkpointer for state persistence
        return workflow.compile(checkpointer=self.checkpointer)

    def _route_after_extraction(self, state: AgentState) -> str:
        """Route after expense extraction based on whether we have valid data"""
        extracted_expense = state.get("extracted_expense", {})

        if extracted_expense and self.expense_service.validate_extracted_expense(
            extracted_expense
        ):
            return "prepare_confirmation"
        else:
            return "llm_call"

    def _route_after_user_response(self, state: AgentState) -> str:
        """Route after user responds to confirmation"""
        user_response = state.get("user_confirmation_response", "")

        # Fallback: if user_confirmation_response is empty, try to get from messages
        if not user_response:
            messages = state.get("messages", [])
            if messages and len(messages) > 0:
                # Get the last human message (user's response)
                for msg in reversed(messages):
                    if isinstance(msg, HumanMessage):
                        user_response = msg.content
                        break

        logger.info(f"Routing after user response: '{user_response}'")

        # Check if user confirms (wants to save)
        if self._is_simple_confirmation(user_response):
            # User confirmed - go to save_expense
            logger.info("User confirmed, routing to save_expense")
            return "save_expense"

        # User wants to make changes - detect intent
        logger.info("User wants changes, routing to detect_update_intent")
        return "detect_update_intent"

    def _route_after_intent(self, state: AgentState) -> str:
        """Route after detecting update intent"""
        wants_update = state.get("wants_update", False)
        corrections = state.get("corrections", {})
        user_response = state.get("user_confirmation_response", "")

        # Fallback: if user_confirmation_response is empty, try to get from messages
        if not user_response:
            messages = state.get("messages", [])
            if messages and len(messages) > 0:
                for msg in reversed(messages):
                    if isinstance(msg, HumanMessage):
                        user_response = msg.content
                        break

        logger.info(
            f"Routing after intent detection: wants_update={wants_update}, corrections={corrections}, user_response='{user_response}'"
        )

        # If user wants update and we have corrections, process them
        if wants_update and corrections:
            logger.info("User wants update with corrections, routing to process_update")
            return "process_update"

        # If user wants update but no corrections parsed, might be parsing error
        # Check if user message contains change keywords
        if wants_update and not corrections:
            user_lower = user_response.lower() if user_response else ""
            change_keywords = ["sửa", "thay", "đổi", "chỉnh", "thành"]
            if any(kw in user_lower for kw in change_keywords):
                # Likely parsing error, try to process anyway
                logger.warning(
                    f"Update intent detected but no corrections parsed. User message: {user_response}"
                )
                return "process_update"
            else:
                # LLM might have parsed wrong - check if it's actually a confirmation
                if self._is_simple_confirmation(user_response):
                    logger.warning(
                        f"LLM parsed as update but user response is confirmation. User message: {user_response}"
                    )
                    return "save_expense"

        # If user confirmed (no update wanted), save
        if not wants_update:
            logger.info("User confirmed, routing to save_expense")
            return "save_expense"

        # Fallback: if unclear, check if it's actually a confirmation
        if self._is_simple_confirmation(user_response):
            logger.info(
                "Unclear intent but user response is confirmation, routing to save_expense"
            )
            return "save_expense"

        # Fallback: if unclear, go to llm_call for clarification
        logger.warning(
            f"Unclear intent, routing to llm_call. User message: {user_response}"
        )
        return "llm_call"

    def _route_after_update(self, state: AgentState) -> str:
        """Route after processing update - go back to ask_confirmation for re-confirmation"""
        return "ask_confirmation"

    def _route_after_save(self, state: AgentState) -> str:
        """Route after saving expense - check budget warning"""
        budget_warning = state.get("budget_warning")
        return "generate_advice" if budget_warning else "end"

    def _normalize_date_format(self, date_str: str) -> str:
        """
        Normalize date string to YYYY-MM-DD format

        Handles various Vietnamese date formats:
        - DD/MM/YYYY -> YYYY-MM-DD
        - DD-MM-YYYY -> YYYY-MM-DD
        - DD.MM.YYYY -> YYYY-MM-DD
        - Already YYYY-MM-DD -> unchanged
        """
        if not date_str:
            return date_str

        import re

        # Already in YYYY-MM-DD format
        if re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
            return date_str

        # DD/MM/YYYY or DD-MM-YYYY or DD.MM.YYYY format
        match = re.match(r'^(\d{1,2})[/\-\.](\d{1,2})[/\-\.](\d{4})$', date_str)
        if match:
            day, month, year = match.groups()
            return f"{year}-{month.zfill(2)}-{day.zfill(2)}"

        # DD/MM/YY format (assume 20XX for year)
        match = re.match(r'^(\d{1,2})[/\-\.](\d{1,2})[/\-\.](\d{2})$', date_str)
        if match:
            day, month, year = match.groups()
            full_year = f"20{year}"
            return f"{full_year}-{month.zfill(2)}-{day.zfill(2)}"

        # If can't parse, return as-is (let the database handle it or error out)
        logger.warning(f"Could not normalize date format: {date_str}")
        return date_str

    def _is_simple_confirmation(self, user_response: str) -> bool:
        """Check if user response is a simple confirmation (no changes)

        Context: User was asked "Bạn có muốn thay đổi thông tin nào không?"
        - "có" = yes, wants changes
        - "không" = no, no changes needed
        """
        if not user_response:
            logger.debug("Empty user response, treating as confirmation")
            return True

        user_response_lower = user_response.lower().strip()
        # Remove punctuation for better matching
        user_response_clean = re.sub(r'[.,!?;:]+$', '', user_response_lower).strip()

        logger.debug(
            f"Checking confirmation for: '{user_response}' (cleaned: '{user_response_clean}')"
        )

        # Keywords indicating no changes wanted (user is satisfied)
        confirmation_keywords = [
            "không",
            "không có",
            "không cần",
            "không cần sửa",
            "không cần thay đổi",
            "giữ nguyên",
            "ok",
            "oke",
            "okay",
            "được rồi",
            "đúng rồi",
            "đúng",
            "ổn",
            "tốt",
            "xong",
            "lưu",
            "xác nhận",
            "đồng ý",
        ]

        # Keywords indicating changes wanted (user wants to modify)
        change_keywords = [
            "có",  # "có" means "yes" - wants to change
            "muốn",
            "sửa",
            "thay",
            "đổi",
            "chỉnh",
            "lại",
            "khác",
            "sai",
            "thành",
            "thay đổi",
        ]

        # If contains change keywords, not a simple confirmation
        if any(kw in user_response_clean for kw in change_keywords):
            logger.debug(f"Found change keyword, not a confirmation")
            return False

        # Check exact match first (for short responses like "ok")
        if user_response_clean in [
            "ok",
            "oke",
            "okay",
            "đúng",
            "ổn",
            "tốt",
            "xong",
            "lưu",
        ]:
            logger.debug(f"Exact match with confirmation keyword")
            return True

        # If contains confirmation keywords, it's a simple confirmation
        if any(kw in user_response_clean for kw in confirmation_keywords):
            logger.debug(f"Found confirmation keyword")
            return True

        # Default: if unclear, assume user wants to make changes
        # Let the LLM detect the actual intent
        logger.debug(f"No clear confirmation, treating as wanting changes")
        return False

    def run(
        self,
        user_message: str,
        user_id: str,
        session_id: str,
        message_type: str = "text",
        image_file: Optional[Any] = None,
    ) -> Dict:
        """Run the AI agent with the given input - may result in interrupt

        Args:
            user_message: User message text
            user_id: User ID
            session_id: Session ID
            message_type: Type of message ('text' or 'image')
            image_file: Image file object (BytesIO) for image messages
        """
        config = {"configurable": {"thread_id": session_id}}

        # Store image_file temporarily (not in state - not serializable)
        if image_file and message_type == "image":
            self._image_files[session_id] = image_file

        initial_state = {
            "messages": [HumanMessage(content=user_message)],
            "user_id": user_id,
            "session_id": session_id,
            "message_type": message_type,
            # NOTE: db_session and image_file are NOT in state - use self.db_session and self._image_files
            "saved_expense": {},
            "asking_confirmation": False,
            "awaiting_user_response": False,
            "user_confirmation_response": "",
            "wants_update": False,
            "corrections": {},
            "extracted_expense": {},
            "budget_warning": {},
            "financial_advice": {},
        }

        result = self.graph.invoke(initial_state, config)

        # Check if interrupted
        interrupt_list = result.get("__interrupt__", [])
        if interrupt_list and len(interrupt_list) > 0:
            interrupt_info = interrupt_list[0]
            interrupt_value = (
                interrupt_info.value
                if hasattr(interrupt_info, "value")
                else interrupt_info
            )

            # Helper to convert empty dict to None
            def none_if_empty(val):
                if val is None or val == {} or val == []:
                    return None
                return val

            return {
                "response": interrupt_value.get(
                    "message", "Chi tiêu đã được lưu. Bạn có muốn thay đổi gì không?"
                ),
                "interrupted": True,
                "saved_expense": none_if_empty(interrupt_value.get("saved_expense")),
                "asking_confirmation": True,
                "extracted_expense": none_if_empty(result.get("extracted_expense")),
                "budget_warning": none_if_empty(result.get("budget_warning")),
                "financial_advice": none_if_empty(result.get("financial_advice")),
            }

        return self._format_result(result)

    def resume(self, session_id: str, user_response: str) -> Dict:
        """Resume after user responds to confirmation"""
        config = {"configurable": {"thread_id": session_id}}

        # Resume with user response
        result = self.graph.invoke(Command(resume=user_response), config)

        return self._format_result(result)

    def _format_result(self, result: Dict) -> Dict:
        """Format graph result into standard response format"""
        # Extract the final AI response - check for non-empty messages list
        messages = result.get("messages", [])
        if messages and len(messages) > 0:
            final_message = messages[-1].content
        else:
            final_message = "Tôi xin lỗi, tôi không thể xử lý yêu cầu của bạn."

        # Helper to convert empty dict to None
        def none_if_empty(val):
            if val is None or val == {} or val == []:
                return None
            return val

        return {
            "response": final_message,
            "interrupted": False,
            "extracted_expense": none_if_empty(result.get("extracted_expense")),
            "budget_warning": none_if_empty(result.get("budget_warning")),
            "financial_advice": none_if_empty(result.get("financial_advice")),
            "saved_expense": none_if_empty(result.get("saved_expense")),
            "asking_confirmation": result.get("asking_confirmation", False),
        }


# Example usage function
def create_ai_agent(db_session: Session):
    """Factory function to create an AI agent instance"""
    return LangGraphAIAgent(db_session)
