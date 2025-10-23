"""
LangGraph implementation for the AI financial assistant
"""

from typing import Dict, List, TypedDict, Annotated, Union
import operator
import json
import logging
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END
from langchain_core.tools import tool
from src.services.expense_processing_service import ExpenseProcessingService
from src.services.budget_management_service import BudgetManagementService
from src.services.financial_advice_service import FinancialAdviceService
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class AgentState(TypedDict):
    """State for the AI financial agent"""

    messages: Annotated[List[BaseMessage], operator.add]
    user_id: str
    session_id: str
    extracted_expense: Dict
    budget_warning: Dict
    financial_advice: Dict
    db_session: Session
    saved_expense: Dict
    asking_confirmation: bool
    awaiting_user_response: bool


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

    def __init__(self, db_session: Session):
        self.db_session = db_session
        self.expense_service = ExpenseProcessingService(db_session)
        self.budget_service = BudgetManagementService(db_session)
        self.advice_service = FinancialAdviceService()

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

        # Build graph
        self.graph = self._build_graph()

    def _extract_expense(self, state: AgentState) -> Dict:
        """Extract expense from user message using the service"""
        user_message = state["messages"][-1].content
        message_type = state.get("message_type", "text")
        user_id = state.get("user_id")

        extracted_expense = None
        if message_type == "text":
            extracted_expense = self.expense_service.extract_expense_from_text(
                user_message, user_id=user_id
            )
        elif message_type == "image":
            # Assuming user_message contains image path for this implementation
            extracted_expense = self.expense_service.extract_expense_from_image(
                user_message
            )

        return {"extracted_expense": extracted_expense}

    def _process_expense_confirmation(self, state: AgentState) -> Dict:
        """Confirm and save the extracted expense"""
        expense_data = state.get("extracted_expense", {})
        user_id = state["user_id"]

        if expense_data:
            expense, budget_warning = self.expense_service.save_expense(
                user_id=user_id,
                expense_data=expense_data,
                category_id=expense_data.get("category_id"),
                source_type="text",
            )

            return {
                "extracted_expense": expense_data,
                "saved_expense": {
                    "id": str(expense.id) if hasattr(expense, 'id') else None,
                    "merchant_name": (
                        expense.merchant_name
                        if hasattr(expense, 'merchant_name')
                        else expense_data.get("merchant_name")
                    ),
                    "amount": (
                        expense.amount
                        if hasattr(expense, 'amount')
                        else expense_data.get("amount")
                    ),
                    "date": (
                        str(expense.date)
                        if hasattr(expense, 'date')
                        else expense_data.get("date")
                    ),
                    "category_id": (
                        expense.category_id
                        if hasattr(expense, 'category_id')
                        else expense_data.get("category_id")
                    ),
                },
                "budget_warning": budget_warning,
                "asking_confirmation": True,
                "awaiting_user_response": True,
            }

        return {}

    def _ask_confirmation(self, state: AgentState) -> Dict:
        """Ask user if they want to make any changes to the saved expense"""
        saved_expense = state.get("saved_expense", {})

        if not saved_expense:
            return {
                "messages": [
                    AIMessage(
                        content="Chi tiêu đã được lưu. Còn gì khác tôi có thể giúp bạn?"
                    )
                ]
            }

        # Format the saved expense information
        expense_summary = f"""
Tôi đã lưu các thông tin chi tiêu sau vào hệ thống:

📌 **Thông tin chi tiêu:**
   • Cửa hàng: {saved_expense.get('merchant_name', 'N/A')}
   • Số tiền: {saved_expense.get('amount', 0):,.0f}đ
   • Ngày: {saved_expense.get('date', 'N/A')}
   • Danh mục: {saved_expense.get('category_id', 'N/A')}

Bạn có muốn thay đổi thông tin nào không? (Nếu có, hãy cho tôi biết chi tiết thay đổi)
        """

        return {"messages": [AIMessage(content=expense_summary.strip())]}

    def _detect_update_intent(self, state: AgentState) -> Dict:
        """Detect if user wants to update the expense using lite model"""
        user_message = state["messages"][-1].content

        try:
            intent_prompt = f"""Phân tích ý định của người dùng:

Người dùng vừa được thông báo rằng chi tiêu đã được lưu và hỏi có muốn thay đổi không.
Bây giờ người dùng trả lời: "{user_message}"

Hãy xác định:
1. Người dùng có muốn chỉnh sửa thông tin không? (yes/no)
2. Nếu có, hãy trích xuất những thay đổi mà người dùng muốn:
   - merchant_name: (tên cửa hàng mới nếu có)
   - amount: (số tiền mới nếu có)
   - date: (ngày mới nếu có)
   
Trả về JSON format:
{{
  "wants_update": true/false,
  "corrections": {{
    "merchant_name": "...",
    "amount": 123.45,
    "date": "YYYY-MM-DD"
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
                return {
                    "wants_update": intent_data.get("wants_update", False),
                    "corrections": intent_data.get("corrections", {}),
                }
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse intent response: {str(e)}")
                # Fallback: check for keywords
                keywords_update = ["thay", "sửa", "đổi", "chỉnh", "lại", "khác", "sai"]
                wants_update = any(kw in user_message.lower() for kw in keywords_update)
                return {"wants_update": wants_update, "corrections": {}}

        except Exception as e:
            logger.error(f"Error detecting update intent: {str(e)}")
            return {"wants_update": False, "corrections": {}}

    def _process_update(self, state: AgentState) -> Dict:
        """Process the expense update"""
        saved_expense = state.get("saved_expense", {})
        intent_result = state.get("intent_result", {})
        corrections = intent_result.get("corrections", {})

        if not saved_expense or not corrections:
            return {
                "messages": [
                    AIMessage(
                        content="Tôi không hiểu những thay đổi bạn muốn thực hiện. Có thể hãy nói rõ hơn nhé?"
                    )
                ]
            }

        try:
            # Apply corrections
            updated_expense, budget_warning = self.expense_service.update_expense(
                expense_id=saved_expense.get("id"),
                user_id=state["user_id"],
                corrections=corrections,
                store_learning=True,
                return_budget_warning=True,
            )

            # Build confirmation message
            response_parts = ["✅ Tôi đã cập nhật chi tiêu với các thay đổi sau:"]

            if "merchant_name" in corrections:
                response_parts.append(f"   • Cửa hàng: {corrections['merchant_name']}")
            if "amount" in corrections:
                response_parts.append(f"   • Số tiền: {corrections['amount']:,.0f}đ")
            if "date" in corrections:
                response_parts.append(f"   • Ngày: {corrections['date']}")

            response_parts.append("\nThông tin đã được lưu lại vào hệ thống.")

            # Add budget warning if applicable
            if budget_warning:
                response_parts.append(
                    f"\n⚠️ {budget_warning.get('message', 'Cảnh báo ngân sách')}"
                )

            response_text = "\n".join(response_parts)

            logger.info(f"Expense updated successfully: {saved_expense.get('id')}")

            return {
                "messages": [AIMessage(content=response_text)],
                "budget_warning": budget_warning,
            }

        except Exception as e:
            logger.error(f"Error processing update: {str(e)}")
            return {
                "messages": [
                    AIMessage(content=f"Xin lỗi, tôi gặp lỗi khi cập nhật: {str(e)}")
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
        response = self.model_with_tools.invoke(state["messages"])
        return {"messages": [response]}

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow"""
        workflow = StateGraph(AgentState)

        # Add nodes
        workflow.add_node("extract_expense", self._extract_expense)
        workflow.add_node("process_confirmation", self._process_expense_confirmation)
        workflow.add_node("ask_confirmation", self._ask_confirmation)
        workflow.add_node("detect_update_intent", self._detect_update_intent)
        workflow.add_node("process_update", self._process_update)
        workflow.add_node("generate_advice", self._generate_financial_advice)
        workflow.add_node("llm_call", self._call_model)

        # Set entry point
        workflow.set_entry_point("extract_expense")

        # Add conditional edges based on tool calls
        workflow.add_conditional_edges(
            "extract_expense",
            self._route_after_extraction,
            {"process_confirmation": "process_confirmation", "llm_call": "llm_call"},
        )

        workflow.add_conditional_edges(
            "process_confirmation",
            self._route_after_confirmation,
            {
                "ask_confirmation": "ask_confirmation",
                "generate_advice": "generate_advice",
                "llm_call": "llm_call",
            },
        )

        # After asking confirmation, always go to llm_call to wait for user response
        workflow.add_edge("ask_confirmation", "llm_call")

        workflow.add_conditional_edges(
            "generate_advice", lambda x: "llm_call", {"llm_call": "llm_call"}
        )

        workflow.add_edge("llm_call", END)

        return workflow.compile()

    def _route_after_extraction(self, state: AgentState) -> str:
        """Route after expense extraction based on whether we have valid data"""
        extracted_expense = state.get("extracted_expense", {})

        if extracted_expense and self.expense_service.validate_extracted_expense(
            extracted_expense
        ):
            return "process_confirmation"
        else:
            return "llm_call"

    def _route_after_confirmation(self, state: AgentState) -> str:
        """Route after expense confirmation based on budget status"""
        # First priority: ask for confirmation if expense was just saved
        if state.get("asking_confirmation", False):
            return "ask_confirmation"

        budget_warning = state.get("budget_warning", None)

        if budget_warning:
            return "generate_advice"
        else:
            return "llm_call"

    def run(
        self,
        user_message: str,
        user_id: str,
        session_id: str,
        message_type: str = "text",
    ) -> Dict:
        """Run the AI agent with the given input"""
        initial_state = {
            "messages": [HumanMessage(content=user_message)],
            "user_id": user_id,
            "session_id": session_id,
            "message_type": message_type,
            "db_session": self.db_session,
            "saved_expense": {},
            "asking_confirmation": False,
            "awaiting_user_response": False,
        }

        result = self.graph.invoke(initial_state)

        # Extract the final AI response
        final_message = (
            result["messages"][-1].content
            if result["messages"]
            else "Tôi xin lỗi, tôi không thể xử lý yêu cầu của bạn."
        )

        return {
            "response": final_message,
            "extracted_expense": result.get("extracted_expense"),
            "budget_warning": result.get("budget_warning"),
            "financial_advice": result.get("financial_advice"),
            "saved_expense": result.get("saved_expense"),
            "asking_confirmation": result.get("asking_confirmation", False),
        }


# Example usage function
def create_ai_agent(db_session: Session):
    """Factory function to create an AI agent instance"""
    return LangGraphAIAgent(db_session)
