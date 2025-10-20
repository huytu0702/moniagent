"""
LangGraph implementation for the AI financial assistant
"""

from typing import Dict, List, TypedDict, Annotated, Union
import operator
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END
from langchain_core.tools import tool
from src.services.expense_processing_service import ExpenseProcessingService
from src.services.budget_management_service import BudgetManagementService
from src.services.financial_advice_service import FinancialAdviceService
from sqlalchemy.orm import Session


class AgentState(TypedDict):
    """State for the AI financial agent"""

    messages: Annotated[List[BaseMessage], operator.add]
    user_id: str
    session_id: str
    extracted_expense: Dict
    budget_warning: Dict
    financial_advice: Dict
    db_session: Session


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

        # Initialize LLM
        self.model = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.1)

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

            return {"extracted_expense": expense_data, "budget_warning": budget_warning}

        return {}

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
            {"generate_advice": "generate_advice", "llm_call": "llm_call"},
        )

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
        }

        result = self.graph.invoke(initial_state)

        # Extract the final AI response
        final_message = (
            result["messages"][-1].content
            if result["messages"]
            else "I'm sorry, I couldn't process that."
        )

        return {
            "response": final_message,
            "extracted_expense": result.get("extracted_expense"),
            "budget_warning": result.get("budget_warning"),
            "financial_advice": result.get("financial_advice"),
        }


# Example usage function
def create_ai_agent(db_session: Session):
    """Factory function to create an AI agent instance"""
    return LangGraphAIAgent(db_session)
