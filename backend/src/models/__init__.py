"""
Models module - import all models to ensure SQLAlchemy relationships are properly initialized
"""

from src.models.user import User
from src.models.invoice import Invoice
from src.models.expense import Expense
from src.models.category import Category
from src.models.ai_interaction import AIInteraction
from src.models.categorization_feedback import CategorizationFeedback
from src.models.expense_categorization_rule import ExpenseCategorizationRule
from src.models.budget import Budget
from src.models.chat_session import ChatSession, ChatMessage
from src.models.expense_category import ExpenseCategory

__all__ = [
    "User",
    "Invoice",
    "Expense",
    "Category",
    "AIInteraction",
    "CategorizationFeedback",
    "ExpenseCategorizationRule",
    "Budget",
    "ChatSession",
    "ChatMessage",
    "ExpenseCategory",
]
