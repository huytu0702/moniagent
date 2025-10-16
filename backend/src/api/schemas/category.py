from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class CategoryResponse(BaseModel):
    """Response model for a single category"""

    id: str
    user_id: str
    name: str
    description: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    is_system_category: bool = False
    display_order: int = 0
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class CategoryListResponse(BaseModel):
    """Response model for list of categories"""

    categories: List[CategoryResponse]


class CreateCategoryRequest(BaseModel):
    """Request model for creating a category"""

    name: str
    description: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    display_order: int = 0


class UpdateCategoryRequest(BaseModel):
    """Request model for updating a category"""

    name: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    display_order: Optional[int] = None


class CategorizationRuleResponse(BaseModel):
    """Response model for a categorization rule"""

    id: str
    user_id: str
    category_id: str
    store_name_pattern: str
    rule_type: str = "keyword"
    confidence_threshold: float = 0.8
    is_active: bool = True
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class CategorizationRuleListResponse(BaseModel):
    """Response model for list of categorization rules"""

    rules: List[CategorizationRuleResponse]


class CreateCategorizationRuleRequest(BaseModel):
    """Request model for creating a categorization rule"""

    category_id: str
    store_name_pattern: str
    rule_type: str = "keyword"  # keyword, regex, exact_match
    confidence_threshold: float = 0.8


class UpdateCategorizationRuleRequest(BaseModel):
    """Request model for updating a categorization rule"""

    category_id: Optional[str] = None
    store_name_pattern: Optional[str] = None
    rule_type: Optional[str] = None
    confidence_threshold: Optional[float] = None
    is_active: Optional[bool] = None


class CategorizationFeedbackResponse(BaseModel):
    """Response model for categorization feedback"""

    id: str
    user_id: str
    expense_id: str
    suggested_category_id: Optional[str] = None
    confirmed_category_id: str
    confidence_score: Optional[float] = None
    feedback_type: str = "confirmation"
    created_at: Optional[str] = None


class CategorizationSuggestionResponse(BaseModel):
    """Response model for category suggestions"""

    suggested_category_id: str
    suggested_category_name: str
    confidence_score: float
    reason: Optional[str] = None


class CategorizeExpenseRequest(BaseModel):
    """Request model for categorizing an expense"""

    expense_id: str
    category_id: Optional[str] = None  # If provided, confirms/corrects the suggestion


class CategorizeExpenseResponse(BaseModel):
    """Response model for expense categorization"""

    expense_id: str
    category_id: str
    category_name: str
    confidence_score: Optional[float] = None
    is_user_confirmed: bool = False


__all__ = [
    "CategoryResponse",
    "CategoryListResponse",
    "CreateCategoryRequest",
    "UpdateCategoryRequest",
    "CategorizationRuleResponse",
    "CategorizationRuleListResponse",
    "CreateCategorizationRuleRequest",
    "UpdateCategorizationRuleRequest",
    "CategorizationFeedbackResponse",
    "CategorizationSuggestionResponse",
    "CategorizeExpenseRequest",
    "CategorizeExpenseResponse",
]
