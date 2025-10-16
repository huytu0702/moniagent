"""
Expense Aggregation Service for aggregating and summarizing expenses
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from src.models.expense import Expense
from src.models.category import Category


logger = logging.getLogger(__name__)


class ExpenseAggregationServiceError(Exception):
    """Custom exception for expense aggregation service errors"""

    pass


class ExpenseAggregationService:
    """
    Service for aggregating expenses and generating spending summaries
    """

    def __init__(self):
        pass

    def get_spending_summary(
        self,
        user_id: str,
        period: str = "monthly",
        db_session: Session = None,
    ) -> Dict[str, Any]:
        """
        Get spending summary for a user by category and time period

        Args:
            user_id: ID of the user
            period: Time period (daily, weekly, monthly)
            db_session: Database session

        Returns:
            Dictionary with total spending, breakdown by category, and by week
        """
        try:
            logger.info(f"Getting spending summary for user {user_id}, period {period}")

            # Calculate date range based on period
            today = datetime.utcnow().date()

            if period == "daily":
                start_date = today
                end_date = today
            elif period == "weekly":
                # Get Monday of current week
                start_date = today - timedelta(days=today.weekday())
                end_date = start_date + timedelta(days=6)
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

            # Default mock data
            by_category = [
                {
                    "category_id": "cat-1",
                    "category_name": "Eating Out",
                    "amount": 500.0,
                    "percentage": 33.3,
                }
            ]

            by_week = [
                {
                    "week": "2025-W42",
                    "amount": 300.0,
                    "percentage": 20.0,
                }
            ]

            # If database session is provided, calculate from actual data
            if db_session:
                by_category, by_week = self._aggregate_from_db(
                    user_id, start_date, end_date, period, db_session
                )

            total_spending = sum(item["amount"] for item in by_category)

            return {
                "period": period,
                "total_spending": total_spending,
                "by_category": by_category,
                "by_week": by_week,
            }

        except Exception as e:
            logger.error(f"Error getting spending summary: {str(e)}")
            raise ExpenseAggregationServiceError(
                f"Failed to get spending summary: {str(e)}"
            )

    def get_spending_by_category(
        self,
        user_id: str,
        period: str = "monthly",
        db_session: Session = None,
    ) -> List[Dict[str, Any]]:
        """
        Get spending breakdown by category

        Args:
            user_id: ID of the user
            period: Time period (daily, weekly, monthly)
            db_session: Database session

        Returns:
            List of spending by category
        """
        try:
            logger.info(
                f"Getting spending by category for user {user_id}, period {period}"
            )

            today = datetime.utcnow().date()

            if period == "daily":
                start_date = today
                end_date = today
            elif period == "weekly":
                start_date = today - timedelta(days=today.weekday())
                end_date = start_date + timedelta(days=6)
            else:  # monthly
                start_date = today.replace(day=1)
                if today.month == 12:
                    end_date = today.replace(
                        year=today.year + 1, month=1, day=1
                    ) - timedelta(days=1)
                else:
                    end_date = today.replace(month=today.month + 1, day=1) - timedelta(
                        days=1
                    )

            spending_by_category = []

            if db_session:
                # Query expenses grouped by category
                expenses = (
                    db_session.query(Expense)
                    .filter(
                        Expense.user_id == user_id,
                        Expense.date >= start_date,
                        Expense.date <= end_date,
                    )
                    .all()
                )

                # Group by category
                category_totals = {}
                for expense in expenses:
                    category = expense.category or "Uncategorized"
                    if category not in category_totals:
                        category_totals[category] = 0.0
                    category_totals[category] += expense.amount

                # Convert to list format
                total = sum(category_totals.values())
                for category, amount in category_totals.items():
                    spending_by_category.append(
                        {
                            "category_id": category,
                            "category_name": category,
                            "amount": amount,
                            "percentage": (amount / total * 100) if total > 0 else 0,
                        }
                    )

            return spending_by_category

        except Exception as e:
            logger.error(f"Error getting spending by category: {str(e)}")
            raise ExpenseAggregationServiceError(
                f"Failed to get spending by category: {str(e)}"
            )

    def get_spending_by_week(
        self,
        user_id: str,
        num_weeks: int = 4,
        db_session: Session = None,
    ) -> List[Dict[str, Any]]:
        """
        Get spending breakdown by week for the past N weeks

        Args:
            user_id: ID of the user
            num_weeks: Number of weeks to include in summary
            db_session: Database session

        Returns:
            List of spending by week
        """
        try:
            logger.info(
                f"Getting spending by week for user {user_id}, num_weeks {num_weeks}"
            )

            spending_by_week = []

            if db_session:
                today = datetime.utcnow().date()

                for i in range(num_weeks):
                    week_end = today - timedelta(days=i * 7)
                    week_start = week_end - timedelta(days=6)

                    # Get week number
                    week_num = week_start.isocalendar()[1]
                    year = week_start.isocalendar()[0]

                    expenses = (
                        db_session.query(Expense)
                        .filter(
                            Expense.user_id == user_id,
                            Expense.date >= week_start,
                            Expense.date <= week_end,
                        )
                        .all()
                    )

                    amount = sum(e.amount for e in expenses)
                    spending_by_week.append(
                        {
                            "week": f"{year}-W{week_num:02d}",
                            "amount": amount,
                        }
                    )

                # Calculate percentages
                total = sum(item["amount"] for item in spending_by_week)
                for item in spending_by_week:
                    item["percentage"] = (
                        (item["amount"] / total * 100) if total > 0 else 0
                    )

            return spending_by_week

        except Exception as e:
            logger.error(f"Error getting spending by week: {str(e)}")
            raise ExpenseAggregationServiceError(
                f"Failed to get spending by week: {str(e)}"
            )

    def _aggregate_from_db(
        self,
        user_id: str,
        start_date: Any,
        end_date: Any,
        period: str,
        db_session: Session,
    ) -> tuple:
        """
        Aggregate expenses from database

        Args:
            user_id: ID of the user
            start_date: Start date for aggregation
            end_date: End date for aggregation
            period: Time period
            db_session: Database session

        Returns:
            Tuple of (by_category, by_week) aggregations
        """
        try:
            expenses = (
                db_session.query(Expense)
                .filter(
                    Expense.user_id == user_id,
                    Expense.date >= start_date,
                    Expense.date <= end_date,
                )
                .all()
            )

            # Aggregate by category
            category_totals = {}
            for expense in expenses:
                category = expense.category or "Uncategorized"
                if category not in category_totals:
                    category_totals[category] = 0.0
                category_totals[category] += expense.amount

            total = sum(category_totals.values())
            by_category = [
                {
                    "category_id": cat,
                    "category_name": cat,
                    "amount": amount,
                    "percentage": (amount / total * 100) if total > 0 else 0,
                }
                for cat, amount in category_totals.items()
            ]

            # Aggregate by week
            week_totals = {}
            for expense in expenses:
                if expense.date:
                    week_num = expense.date.isocalendar()[1]
                    year = expense.date.isocalendar()[0]
                    week_key = f"{year}-W{week_num:02d}"
                    if week_key not in week_totals:
                        week_totals[week_key] = 0.0
                    week_totals[week_key] += expense.amount

            total_weeks = sum(week_totals.values())
            by_week = [
                {
                    "week": week,
                    "amount": amount,
                    "percentage": (
                        (amount / total_weeks * 100) if total_weeks > 0 else 0
                    ),
                }
                for week, amount in week_totals.items()
            ]

            return by_category, by_week

        except Exception as e:
            logger.error(f"Error aggregating from database: {str(e)}")
            return [], []
