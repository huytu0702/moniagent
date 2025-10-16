"""
Expense API router for managing expenses
Includes CRUD operations and corrections (User Story 2)
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from src.core.database import get_db
from src.core.security import get_current_user
from src.services.expense_processing_service import ExpenseProcessingService
from src.utils.exceptions import ValidationError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/expenses", tags=["expenses"])


# ===== Schemas =====
class ExpenseResponse(BaseModel):
    """Response model for expense data"""

    id: str
    user_id: str
    merchant_name: Optional[str]
    amount: float
    date: Optional[str]
    category_id: Optional[str]
    description: Optional[str]
    confirmed_by_user: bool
    source_type: Optional[str]
    created_at: str
    updated_at: str


class ExpenseListResponse(BaseModel):
    """Response model for list of expenses"""

    expenses: List[ExpenseResponse]


class ExpenseUpdateRequest(BaseModel):
    """Request model for updating/correcting an expense"""

    merchant_name: Optional[str] = Field(None, description="Corrected merchant name")
    amount: Optional[float] = Field(None, description="Corrected amount", gt=0)
    date: Optional[str] = Field(None, description="Corrected date (YYYY-MM-DD)")
    category_id: Optional[str] = Field(None, description="Corrected category ID")


class ExpenseUpdateResponse(BaseModel):
    """Response model after updating an expense"""

    id: str
    merchant_name: Optional[str]
    amount: float
    date: Optional[str]
    category_id: Optional[str]
    confirmed_by_user: bool
    message: str
    budget_warning: Optional[dict] = None


class ExpenseDeleteResponse(BaseModel):
    """Response model for expense deletion"""

    message: str
    expense_id: str


class ExpenseCreateRequest(BaseModel):
    """Request model for creating an expense"""
    
    merchant_name: Optional[str] = Field(None, description="Name of the merchant/store")
    amount: float = Field(..., gt=0, description="Amount of the expense")
    date: Optional[str] = Field(None, description="Date of expense (YYYY-MM-DD)")
    category_id: Optional[str] = Field(None, description="Category ID")
    description: Optional[str] = Field(None, description="Description of the expense")


# ===== Endpoints =====


@router.post("", response_model=ExpenseResponse)
async def create_expense(
    expense_request: ExpenseCreateRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Create a new expense

    Args:
        expense_request: Expense creation data
        current_user: Current authenticated user
        db: Database session

    Returns:
        Created expense data
    """
    try:
        user_id = current_user.id if hasattr(current_user, "id") else current_user["id"]
        logger.info(f"Creating expense for user {user_id}")
        
        expense_service = ExpenseProcessingService(db)
        
        # Create the expense with the provided data
        created_expense = expense_service.create_expense(
            user_id=user_id,
            merchant_name=expense_request.merchant_name,
            amount=expense_request.amount,
            date=expense_request.date,
            category_id=expense_request.category_id,
            description=expense_request.description,
            source_type="manual"  # Indicating it's a manually entered expense
        )
        
        logger.info(f"Expense created successfully with id {created_expense.id}")
        
        return ExpenseResponse(
            id=created_expense.id,
            user_id=created_expense.user_id,
            merchant_name=created_expense.merchant_name,
            amount=created_expense.amount,
            date=created_expense.date.isoformat() if created_expense.date else None,
            category_id=created_expense.category_id,
            description=created_expense.description,
            confirmed_by_user=created_expense.confirmed_by_user,
            source_type=created_expense.source_type,
            created_at=created_expense.created_at.isoformat(),
            updated_at=created_expense.updated_at.isoformat(),
        )

    except ValidationError as e:
        logger.error(f"Validation error creating expense: {str(e)}")
        raise HTTPException(status_code=422, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating expense: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=ExpenseListResponse)
async def get_expenses(
    category_id: Optional[str] = Query(None, description="Filter by category ID"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get all expenses for the current user

    Args:
        category_id: Optional category filter
        current_user: Current authenticated user
        db: Database session

    Returns:
        List of expenses
    """
    try:
        user_id = current_user.id if hasattr(current_user, "id") else current_user["id"]
        logger.info(f"Fetching expenses for user {user_id}")

        from src.models.expense import Expense

        query = db.query(Expense).filter_by(user_id=user_id)

        if category_id:
            query = query.filter_by(category_id=category_id)

        expenses = query.order_by(Expense.created_at.desc()).all()

        expense_responses = [
            ExpenseResponse(
                id=expense.id,
                user_id=expense.user_id,
                merchant_name=expense.merchant_name,
                amount=expense.amount,
                date=expense.date.isoformat() if expense.date else None,
                category_id=expense.category_id,
                description=expense.description,
                confirmed_by_user=expense.confirmed_by_user,
                source_type=expense.source_type,
                created_at=expense.created_at.isoformat(),
                updated_at=expense.updated_at.isoformat(),
            )
            for expense in expenses
        ]

        return ExpenseListResponse(expenses=expense_responses)

    except Exception as e:
        logger.error(f"Error fetching expenses: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{expense_id}", response_model=ExpenseResponse)
async def get_expense_by_id(
    expense_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get a specific expense by ID

    Args:
        expense_id: Expense ID
        current_user: Current authenticated user
        db: Database session

    Returns:
        Expense data
    """
    try:
        user_id = current_user.id if hasattr(current_user, "id") else current_user["id"]
        logger.info(f"Fetching expense {expense_id} for user {user_id}")

        expense_service = ExpenseProcessingService(db)
        expense = expense_service.get_expense(expense_id)

        # Verify ownership
        if expense.user_id != user_id:
            raise HTTPException(
                status_code=403, detail="Unauthorized access to expense"
            )

        return ExpenseResponse(
            id=expense.id,
            user_id=expense.user_id,
            merchant_name=expense.merchant_name,
            amount=expense.amount,
            date=expense.date.isoformat() if expense.date else None,
            category_id=expense.category_id,
            description=expense.description,
            confirmed_by_user=expense.confirmed_by_user,
            source_type=expense.source_type,
            created_at=expense.created_at.isoformat(),
            updated_at=expense.updated_at.isoformat(),
        )

    except ValidationError as e:
        logger.error(f"Expense not found: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching expense: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{expense_id}", response_model=ExpenseUpdateResponse)
async def update_expense(
    expense_id: str,
    update_request: ExpenseUpdateRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Update/correct an expense (User Story 2)

    Args:
        expense_id: Expense ID to update
        update_request: Update data with corrections
        current_user: Current authenticated user
        db: Database session

    Returns:
        Updated expense data with message
    """
    try:
        user_id = current_user.id if hasattr(current_user, "id") else current_user["id"]
        logger.info(f"Updating expense {expense_id} for user {user_id}")

        expense_service = ExpenseProcessingService(db)

        # Build corrections dictionary from request
        corrections = {}
        if update_request.merchant_name is not None:
            corrections["merchant_name"] = update_request.merchant_name
        if update_request.amount is not None:
            corrections["amount"] = update_request.amount
        if update_request.date is not None:
            corrections["date"] = update_request.date
        if update_request.category_id is not None:
            corrections["category_id"] = update_request.category_id

        if not corrections:
            raise HTTPException(
                status_code=400,
                detail="No corrections provided",
            )

        # Apply corrections
        updated_expense, budget_warning = expense_service.update_expense(
            expense_id=expense_id,
            user_id=user_id,
            corrections=corrections,
            store_learning=True,
            return_budget_warning=True,
        )

        logger.info(f"Expense {expense_id} updated successfully")

        return ExpenseUpdateResponse(
            id=updated_expense.id,
            merchant_name=updated_expense.merchant_name,
            amount=updated_expense.amount,
            date=updated_expense.date.isoformat() if updated_expense.date else None,
            category_id=updated_expense.category_id,
            confirmed_by_user=updated_expense.confirmed_by_user,
            message="Expense updated successfully",
            budget_warning=budget_warning,
        )

    except ValidationError as e:
        if "not found" in str(e).lower():
            logger.error(f"Expense not found: {str(e)}")
            raise HTTPException(status_code=404, detail=str(e))
        elif "unauthorized" in str(e).lower():
            logger.error(f"Unauthorized access: {str(e)}")
            raise HTTPException(status_code=403, detail=str(e))
        else:
            logger.error(f"Validation error: {str(e)}")
            raise HTTPException(status_code=422, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating expense: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{expense_id}", response_model=ExpenseDeleteResponse)
async def delete_expense(
    expense_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Delete an expense

    Args:
        expense_id: Expense ID to delete
        current_user: Current authenticated user
        db: Database session

    Returns:
        Deletion confirmation
    """
    try:
        user_id = current_user.id if hasattr(current_user, "id") else current_user["id"]
        logger.info(f"Deleting expense {expense_id} for user {user_id}")

        from src.models.expense import Expense

        expense = db.query(Expense).filter_by(id=expense_id).first()

        if not expense:
            raise HTTPException(
                status_code=404, detail=f"Expense not found: {expense_id}"
            )

        # Verify ownership
        if expense.user_id != user_id:
            raise HTTPException(
                status_code=403,
                detail="Unauthorized: Cannot delete another user's expense",
            )

        db.delete(expense)
        db.commit()

        logger.info(f"Expense {expense_id} deleted successfully")

        return ExpenseDeleteResponse(
            message="Expense deleted successfully",
            expense_id=expense_id,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting expense: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
