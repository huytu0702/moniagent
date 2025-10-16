"""
Budget management API router
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from src.core.security import get_current_user
from src.core.database import get_db
from src.services.budget_management_service import BudgetManagementService
from src.services.expense_aggregation_service import ExpenseAggregationService
from src.api.schemas.budget import (
    BudgetCreateRequest,
    BudgetUpdateRequest,
    BudgetResponse,
    BudgetAlertResponse,
    SpendingSummaryResponse,
)


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/budgets", tags=["budgets"])


@router.post("", response_model=BudgetResponse, status_code=201)
async def create_budget(
    request: BudgetCreateRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Create a new budget for a category

    Args:
        request: Budget creation request with category_id, limit_amount, etc.
        current_user: Current authenticated user
        db: Database session

    Returns:
        Created budget with calculated spent and remaining amounts
    """
    try:
        logger.info(
            f"Creating budget for user {current_user.id if hasattr(current_user, 'id') else current_user['id']}"
        )

        user_id = current_user.id if hasattr(current_user, 'id') else current_user['id']

        budget_service = BudgetManagementService(db_session=db)
        result = budget_service.create_budget(
            user_id=user_id,
            category_id=request.category_id,
            limit_amount=request.limit_amount,
            period=request.period,
            alert_threshold=request.alert_threshold,
            db_session=db,
        )

        return BudgetResponse(**result)

    except Exception as e:
        logger.error(f"Error creating budget: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/alerts", response_model=list)
async def get_budget_alerts(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get budget alerts for the current user

    Args:
        current_user: Current authenticated user
        db: Database session

    Returns:
        List of budget alerts
    """
    try:
        user_id = current_user.id if hasattr(current_user, 'id') else current_user['id']
        logger.info(f"Checking budget alerts for user {user_id}")

        budget_service = BudgetManagementService(db_session=db)
        alerts = budget_service.check_budget_alerts(user_id=user_id, db_session=db)

        return alerts

    except Exception as e:
        logger.error(f"Error checking budget alerts: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/check/{category_id}")
async def check_budget_status(
    category_id: str,
    amount: float = Query(default=0, description="Amount to check against budget"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Check budget status for a specific category with optional amount

    This endpoint is useful for checking if adding a new expense would
    exceed the budget before actually recording it.

    Args:
        category_id: ID of the expense category
        amount: Optional amount to add to current spending for status check
        current_user: Current authenticated user
        db: Database session

    Returns:
        Budget status with warning if applicable
    """
    try:
        user_id = current_user.id if hasattr(current_user, 'id') else current_user['id']
        logger.info(
            f"Checking budget status for user {user_id}, category {category_id}, amount {amount}"
        )

        budget_service = BudgetManagementService(db_session=db)
        status = budget_service.check_budget_status(
            user_id=user_id,
            category_id=category_id,
            amount=amount,
            db_session=db,
        )

        if status is None:
            # No budget set for this category
            return {
                "category_id": category_id,
                "has_budget": False,
                "message": "No budget set for this category",
            }

        return status

    except Exception as e:
        logger.error(f"Error checking budget status: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=list)
async def get_budgets(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get all budgets for the current user

    Args:
        current_user: Current authenticated user
        db: Database session

    Returns:
        List of budgets with calculated spent and remaining amounts
    """
    try:
        user_id = current_user.id if hasattr(current_user, 'id') else current_user['id']
        logger.info(f"Fetching budgets for user {user_id}")

        budget_service = BudgetManagementService(db_session=db)
        budgets = budget_service.get_user_budgets(user_id=user_id, db_session=db)

        return budgets

    except Exception as e:
        logger.error(f"Error fetching budgets: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{budget_id}", response_model=BudgetResponse)
async def get_budget(
    budget_id: str,
    current_user: dict = Depends(get_current_user),
):
    """
    Get a specific budget by ID

    Args:
        budget_id: ID of the budget
        current_user: Current authenticated user

    Returns:
        Budget details
    """
    try:
        user_id = current_user.id if hasattr(current_user, 'id') else current_user['id']
        logger.info(f"Fetching budget {budget_id} for user {user_id}")

        # This would normally query the database
        # For now, return mock response
        return {
            "id": budget_id,
            "user_id": user_id,
            "category_id": "cat-1",
            "category_name": "Category",
            "limit_amount": 500.0,
            "period": "monthly",
            "spent_amount": 250.0,
            "remaining_amount": 250.0,
            "alert_threshold": 0.8,
            "created_at": "2025-10-16T10:00:00",
            "updated_at": "2025-10-16T10:00:00",
        }

    except Exception as e:
        logger.error(f"Error fetching budget: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{budget_id}", response_model=BudgetResponse)
async def update_budget(
    budget_id: str,
    request: BudgetUpdateRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Update an existing budget

    Args:
        budget_id: ID of the budget to update
        request: Budget update request
        current_user: Current authenticated user
        db: Database session

    Returns:
        Updated budget
    """
    try:
        user_id = current_user.id if hasattr(current_user, 'id') else current_user['id']
        logger.info(f"Updating budget {budget_id} for user {user_id}")

        budget_service = BudgetManagementService(db_session=db)
        result = budget_service.update_budget(
            user_id=user_id,
            budget_id=budget_id,
            limit_amount=request.limit_amount,
            alert_threshold=request.alert_threshold,
            period=request.period,
            db_session=db,
        )

        return BudgetResponse(**result)

    except Exception as e:
        logger.error(f"Error updating budget: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{budget_id}", status_code=204)
async def delete_budget(
    budget_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Delete a budget

    Args:
        budget_id: ID of the budget to delete
        current_user: Current authenticated user
        db: Database session

    Returns:
        No content
    """
    try:
        user_id = current_user.id if hasattr(current_user, 'id') else current_user['id']
        logger.info(f"Deleting budget {budget_id} for user {user_id}")

        budget_service = BudgetManagementService(db_session=db)
        budget_service.delete_budget(
            user_id=user_id, budget_id=budget_id, db_session=db
        )

    except Exception as e:
        logger.error(f"Error deleting budget: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


# Spending summary routes (shared with financial tracking)
spending_router = APIRouter(prefix="/spending", tags=["spending"])


@spending_router.get("/summary", response_model=SpendingSummaryResponse)
async def get_spending_summary(
    period: str = Query(
        default="monthly", description="Period: daily, weekly, monthly"
    ),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get spending summary for the current user

    Args:
        period: Time period (daily, weekly, monthly)
        current_user: Current authenticated user
        db: Database session

    Returns:
        Spending summary with breakdown by category and week
    """
    try:
        user_id = current_user.id if hasattr(current_user, 'id') else current_user['id']
        logger.info(f"Getting spending summary for user {user_id}, period {period}")

        aggregation_service = ExpenseAggregationService()
        summary = aggregation_service.get_spending_summary(
            user_id=user_id, period=period, db_session=db
        )

        return SpendingSummaryResponse(**summary)

    except Exception as e:
        logger.error(f"Error getting spending summary: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
