"""
Budget API schemas and DTOs
"""

from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class BudgetCreateRequest(BaseModel):
    """Request model for creating a budget"""

    category_id: str = Field(..., description="ID of the category for this budget")
    limit_amount: float = Field(..., description="Budget limit amount", gt=0)
    period: str = Field(
        default="monthly", description="Budget period: monthly, weekly, yearly"
    )
    alert_threshold: float = Field(default=0.8, description="Alert threshold (0.0-1.0)")

    class Config:
        json_schema_extra = {
            "example": {
                "category_id": "cat-123",
                "limit_amount": 500.0,
                "period": "monthly",
                "alert_threshold": 0.8,
            }
        }


class BudgetUpdateRequest(BaseModel):
    """Request model for updating a budget"""

    limit_amount: Optional[float] = Field(None, description="New budget limit", gt=0)
    alert_threshold: Optional[float] = Field(None, description="New alert threshold")
    period: Optional[str] = Field(None, description="New period")

    class Config:
        json_schema_extra = {
            "example": {
                "limit_amount": 600.0,
                "alert_threshold": 0.75,
            }
        }


class BudgetResponse(BaseModel):
    """Response model for a budget"""

    id: str
    user_id: str
    category_id: str
    category_name: str
    limit_amount: float
    period: str
    spent_amount: float
    remaining_amount: float
    alert_threshold: float
    created_at: str
    updated_at: str

    class Config:
        json_schema_extra = {
            "example": {
                "id": "budget-123",
                "user_id": "user-456",
                "category_id": "cat-789",
                "category_name": "Eating Out",
                "limit_amount": 500.0,
                "period": "monthly",
                "spent_amount": 250.0,
                "remaining_amount": 250.0,
                "alert_threshold": 0.8,
                "created_at": "2025-10-16T10:00:00",
                "updated_at": "2025-10-16T10:00:00",
            }
        }


class BudgetAlertResponse(BaseModel):
    """Response model for budget alerts"""

    budget_id: str
    category_name: str
    limit_amount: float
    spent_amount: float
    remaining_amount: float
    alert_level: str  # 'warning', 'critical', 'info'
    message: str


class SpendingByCategoryResponse(BaseModel):
    """Response model for spending by category"""

    category_id: str
    category_name: str
    amount: float
    percentage: float


class SpendingByWeekResponse(BaseModel):
    """Response model for spending by week"""

    week: str  # Format: YYYY-Www
    amount: float
    percentage: float


class SpendingSummaryResponse(BaseModel):
    """Response model for spending summary"""

    period: str  # 'daily', 'weekly', 'monthly'
    total_spending: float
    by_category: Optional[List[SpendingByCategoryResponse]] = None
    by_week: Optional[List[SpendingByWeekResponse]] = None

    class Config:
        json_schema_extra = {
            "example": {
                "period": "monthly",
                "total_spending": 1500.0,
                "by_category": [
                    {
                        "category_id": "cat-1",
                        "category_name": "Eating Out",
                        "amount": 500.0,
                        "percentage": 33.3,
                    }
                ],
                "by_week": [
                    {
                        "week": "2025-W42",
                        "amount": 300.0,
                        "percentage": 20.0,
                    }
                ],
            }
        }


class FinancialAdviceResponse(BaseModel):
    """Response model for financial advice"""

    advice: str
    recommendations: List[str]
    spending_pattern: str  # 'low', 'normal', 'high', 'above_average'
    period: str
    top_spending_category: Optional[str] = None
    top_spending_amount: Optional[float] = None

    class Config:
        json_schema_extra = {
            "example": {
                "advice": "You are spending 33% on dining out. Consider cooking at home more.",
                "recommendations": [
                    "Cook at home 4 days a week",
                    "Set a daily dining limit of $20",
                ],
                "spending_pattern": "high",
                "period": "monthly",
                "top_spending_category": "Eating Out",
                "top_spending_amount": 500.0,
            }
        }
