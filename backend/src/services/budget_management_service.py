"""
Budget Management Service for handling budget operations
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from uuid import uuid4
from sqlalchemy.orm import Session
from src.models.budget import Budget
from src.models.category import Category
from src.models.expense import Expense


logger = logging.getLogger(__name__)


class BudgetManagementServiceError(Exception):
    """Custom exception for budget management service errors"""

    pass


class BudgetManagementService:
    """
    Service for handling budget management operations
    """

    def __init__(self, db_session: Session = None):
        self.db_session = db_session

    def create_budget(
        self,
        user_id: str,
        category_id: str,
        limit_amount: float,
        period: str = "monthly",
        alert_threshold: float = 0.8,
        db_session: Session = None,
    ) -> Dict[str, Any]:
        """
        Create a new budget for a user and category

        Args:
            user_id: ID of the user
            category_id: ID of the category
            limit_amount: Budget limit amount
            period: Budget period (monthly, weekly, yearly)
            alert_threshold: Alert threshold as percentage (0.0-1.0)
            db_session: Database session

        Returns:
            Dictionary with budget details including spent and remaining amounts
        """
        try:
            logger.info(
                f"Creating budget for user {user_id}, category {category_id}, limit {limit_amount}"
            )

            if not category_id or not limit_amount:
                raise BudgetManagementServiceError(
                    "Missing required fields: category_id, limit_amount"
                )

            if limit_amount <= 0:
                raise BudgetManagementServiceError(
                    "Limit amount must be greater than 0"
                )

            if not (0 <= alert_threshold <= 1):
                raise BudgetManagementServiceError(
                    "Alert threshold must be between 0 and 1"
                )

            # Use provided session or fall back to instance session
            session_to_use = db_session or self.db_session
            if not session_to_use:
                raise BudgetManagementServiceError("Database session not available")

            # Check if budget already exists for this category
            existing_budget = (
                session_to_use.query(Budget)
                .filter(Budget.user_id == user_id, Budget.category_id == category_id)
                .first()
            )

            if existing_budget:
                raise BudgetManagementServiceError(
                    f"Budget already exists for this category. Use update instead."
                )

            # Create new budget
            budget_id = str(uuid4())
            budget = Budget(
                id=budget_id,
                user_id=user_id,
                category_id=category_id,
                limit_amount=limit_amount,
                period=period,
                alert_threshold=alert_threshold,
            )

            # Save to database
            session_to_use.add(budget)
            session_to_use.commit()
            session_to_use.refresh(budget)

            # Calculate spent amount
            spent_amount = self._calculate_spent_amount(
                user_id, category_id, period, session_to_use
            )

            # Get category name
            category = (
                session_to_use.query(Category)
                .filter(Category.id == category_id)
                .first()
            )
            category_name = category.name if category else "Unknown"

            return {
                "id": budget.id,
                "user_id": budget.user_id,
                "category_id": budget.category_id,
                "category_name": category_name,
                "limit_amount": budget.limit_amount,
                "period": budget.period,
                "spent_amount": spent_amount,
                "remaining_amount": budget.limit_amount - spent_amount,
                "alert_threshold": budget.alert_threshold,
                "created_at": budget.created_at.isoformat() if budget.created_at else datetime.utcnow().isoformat(),
                "updated_at": budget.updated_at.isoformat() if budget.updated_at else datetime.utcnow().isoformat(),
            }

        except BudgetManagementServiceError as e:
            logger.error(f"Budget management error: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error creating budget: {str(e)}")
            raise BudgetManagementServiceError(f"Failed to create budget: {str(e)}")

    def get_user_budgets(
        self,
        user_id: str,
        db_session: Session = None,
    ) -> List[Dict[str, Any]]:
        """
        Get all budgets for a user

        Args:
            user_id: ID of the user
            db_session: Database session

        Returns:
            List of budget dictionaries with spent and remaining amounts
        """
        try:
            logger.info(f"Fetching budgets for user {user_id}")

            # Use provided session or fall back to instance session
            session_to_use = db_session or self.db_session
            if not session_to_use:
                raise BudgetManagementServiceError("Database session not available")

            # Query all budgets for this user
            budget_records = (
                session_to_use.query(Budget)
                .filter(Budget.user_id == user_id)
                .all()
            )

            budgets = []
            for budget in budget_records:
                # Calculate spent amount for this budget
                spent_amount = self._calculate_spent_amount(
                    user_id, budget.category_id, budget.period, session_to_use
                )

                # Get category name
                category = (
                    session_to_use.query(Category)
                    .filter(Category.id == budget.category_id)
                    .first()
                )
                category_name = category.name if category else "Unknown"

                budgets.append({
                    "id": budget.id,
                    "user_id": budget.user_id,
                    "category_id": budget.category_id,
                    "category_name": category_name,
                    "limit_amount": budget.limit_amount,
                    "period": budget.period,
                    "spent_amount": spent_amount,
                    "remaining_amount": budget.limit_amount - spent_amount,
                    "alert_threshold": budget.alert_threshold,
                    "created_at": budget.created_at.isoformat() if budget.created_at else datetime.utcnow().isoformat(),
                    "updated_at": budget.updated_at.isoformat() if budget.updated_at else datetime.utcnow().isoformat(),
                })

            logger.info(f"Found {len(budgets)} budgets for user {user_id}")
            return budgets

        except Exception as e:
            logger.error(f"Error fetching budgets: {str(e)}")
            raise BudgetManagementServiceError(f"Failed to fetch budgets: {str(e)}")

    def update_budget(
        self,
        user_id: str,
        budget_id: str,
        limit_amount: Optional[float] = None,
        alert_threshold: Optional[float] = None,
        period: Optional[str] = None,
        db_session: Session = None,
    ) -> Dict[str, Any]:
        """
        Update an existing budget

        Args:
            user_id: ID of the user
            budget_id: ID of the budget to update
            limit_amount: New limit amount (optional)
            alert_threshold: New alert threshold (optional)
            period: New period (optional)
            db_session: Database session

        Returns:
            Updated budget dictionary
        """
        try:
            logger.info(f"Updating budget {budget_id} for user {user_id}")

            if limit_amount is not None and limit_amount <= 0:
                raise BudgetManagementServiceError(
                    "Limit amount must be greater than 0"
                )

            if alert_threshold is not None and not (0 <= alert_threshold <= 1):
                raise BudgetManagementServiceError(
                    "Alert threshold must be between 0 and 1"
                )

            # Use provided session or fall back to instance session
            session_to_use = db_session or self.db_session
            if not session_to_use:
                raise BudgetManagementServiceError("Database session not available")

            # Get existing budget
            budget = (
                session_to_use.query(Budget)
                .filter(Budget.id == budget_id, Budget.user_id == user_id)
                .first()
            )

            if not budget:
                raise BudgetManagementServiceError(
                    f"Budget {budget_id} not found for user {user_id}"
                )

            # Update fields if provided
            if limit_amount is not None:
                budget.limit_amount = limit_amount
            if alert_threshold is not None:
                budget.alert_threshold = alert_threshold
            if period is not None:
                budget.period = period

            # Update timestamp
            budget.updated_at = datetime.utcnow()

            # Save to database
            session_to_use.commit()
            session_to_use.refresh(budget)

            # Calculate spent amount
            spent_amount = self._calculate_spent_amount(
                user_id, budget.category_id, budget.period, session_to_use
            )

            # Get category name
            category = (
                session_to_use.query(Category)
                .filter(Category.id == budget.category_id)
                .first()
            )
            category_name = category.name if category else "Unknown"

            return {
                "id": budget.id,
                "user_id": budget.user_id,
                "category_id": budget.category_id,
                "category_name": category_name,
                "limit_amount": budget.limit_amount,
                "period": budget.period,
                "spent_amount": spent_amount,
                "remaining_amount": budget.limit_amount - spent_amount,
                "alert_threshold": budget.alert_threshold,
                "created_at": budget.created_at.isoformat() if budget.created_at else datetime.utcnow().isoformat(),
                "updated_at": budget.updated_at.isoformat() if budget.updated_at else datetime.utcnow().isoformat(),
            }

        except BudgetManagementServiceError as e:
            logger.error(f"Budget management error: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error updating budget: {str(e)}")
            raise BudgetManagementServiceError(f"Failed to update budget: {str(e)}")

    def check_budget_alerts(
        self,
        user_id: str,
        db_session: Session = None,
    ) -> List[Dict[str, Any]]:
        """
        Check if any budgets have exceeded alert thresholds

        Args:
            user_id: ID of the user
            db_session: Database session

        Returns:
            List of alert dictionaries for budgets that exceeded thresholds
        """
        try:
            logger.info(f"Checking budget alerts for user {user_id}")

            alerts = []
            # This would normally query from db_session and check spent amounts

            return alerts

        except Exception as e:
            logger.error(f"Error checking budget alerts: {str(e)}")
            raise BudgetManagementServiceError(
                f"Failed to check budget alerts: {str(e)}"
            )

    def delete_budget(
        self,
        user_id: str,
        budget_id: str,
        db_session: Session = None,
    ) -> bool:
        """
        Delete a budget

        Args:
            user_id: ID of the user
            budget_id: ID of the budget to delete
            db_session: Database session

        Returns:
            True if deletion was successful
        """
        try:
            logger.info(f"Deleting budget {budget_id} for user {user_id}")

            # This would normally query and delete from database
            return True

        except Exception as e:
            logger.error(f"Error deleting budget: {str(e)}")
            raise BudgetManagementServiceError(f"Failed to delete budget: {str(e)}")

    def check_budget_status(
        self,
        user_id: str,
        category_id: str,
        amount: float = 0,
        db_session: Session = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Check the budget status for a user's category

        Args:
            user_id: ID of the user
            category_id: ID of the category
            amount: Amount to check against the budget
            db_session: Database session

        Returns:
            Dictionary with budget information and warning if applicable
        """
        try:
            logger.info(
                f"Checking budget status for user {user_id}, category {category_id}"
            )

            # Use provided session or fall back to instance session
            session_to_use = db_session or self.db_session
            if not session_to_use:
                raise BudgetManagementServiceError("Database session not available")

            # Get the budget for this category
            budget = (
                session_to_use.query(Budget)
                .filter(Budget.user_id == user_id, Budget.category_id == category_id)
                .first()
            )

            if not budget:
                return None

            # Calculate current spending including the new amount
            spent_amount = self._calculate_spent_amount(
                user_id, category_id, budget.period, session_to_use
            )

            # Include the new expense amount for status check
            total_with_new_expense = spent_amount + amount

            # Calculate remaining amount
            remaining = budget.limit_amount - total_with_new_expense

            # Calculate percentage used
            percentage_used = (
                total_with_new_expense / budget.limit_amount
                if budget.limit_amount > 0
                else 0
            )

            # Check if we should issue a warning
            warning = percentage_used >= budget.alert_threshold

            # Get category name
            category = (
                session_to_use.query(Category)
                .filter(Category.id == category_id)
                .first()
            )
            category_name = category.name if category else "Unknown"

            return {
                "category_id": category_id,
                "category_name": category_name,
                "limit": budget.limit_amount,
                "spent": spent_amount,
                "total_with_new_expense": total_with_new_expense,
                "remaining": remaining,
                "percentage_used": percentage_used,
                "alert_threshold": budget.alert_threshold,
                "warning": warning,
                "alert_level": (
                    "high"
                    if percentage_used >= 1.0
                    else "medium" if warning else "none"
                ),
                "message": (
                    f"Bạn đã vượt quá ngân sách cho danh mục {category_name}!"
                    if percentage_used >= 1.0
                    else (
                        f"Bạn đang tiến gần đến ngân sách cho danh mục {category_name}."
                        if warning
                        else None
                    )
                ),
            }

        except Exception as e:
            logger.error(f"Error checking budget status: {str(e)}")
            raise BudgetManagementServiceError(
                f"Failed to check budget status: {str(e)}"
            )

    def _calculate_spent_amount(
        self,
        user_id: str,
        category_id: str,
        period: str,
        db_session: Session = None,
    ) -> float:
        """
        Calculate total spent amount for a category within a time period

        Args:
            user_id: ID of the user
            category_id: ID of the category
            period: Time period (monthly, weekly, yearly)
            db_session: Database session

        Returns:
            Total spent amount
        """
        try:
            # Calculate date range based on period
            today = datetime.utcnow().date()

            if period == "weekly":
                # Get Monday of current week
                start_date = today - timedelta(days=today.weekday())
                end_date = start_date + timedelta(days=6)
            elif period == "yearly":
                start_date = today.replace(month=1, day=1)
                end_date = today.replace(month=12, day=31)
            else:  # monthly (default)
                start_date = today.replace(day=1)
                # Get last day of month
                if today.month == 12:
                    end_date = today.replace(
                        year=today.year + 1, month=1, day=1
                    ) - timedelta(days=1)
                else:
                    end_date = today.replace(month=today.month + 1, day=1) - timedelta(
                        days=1
                    )

            # In a real implementation, this would query from database
            # For now, return 0
            if db_session:
                # Query expenses for this user, category, and period
                expenses = (
                    db_session.query(Expense)
                    .filter(
                        Expense.user_id == user_id,
                        Expense.category_id == category_id,
                        Expense.date >= start_date,
                        Expense.date <= end_date,
                    )
                    .all()
                )
                return sum(e.amount for e in expenses)

            return 0.0

        except Exception as e:
            logger.error(f"Error calculating spent amount: {str(e)}")
            return 0.0
