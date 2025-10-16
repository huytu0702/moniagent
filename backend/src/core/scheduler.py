"""
Scheduled tasks for periodic operations like budget alerts and data aggregation.
"""

import logging
from typing import Callable, List, Dict, Any
from datetime import datetime, timedelta
import asyncio
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class ScheduledTask(ABC):
    """Base class for scheduled tasks."""

    def __init__(self, name: str, interval_seconds: int):
        """
        Initialize a scheduled task.

        Args:
            name: Name of the task
            interval_seconds: How often to run (in seconds)
        """
        self.name = name
        self.interval_seconds = interval_seconds
        self.next_run = datetime.utcnow()
        self.last_run: datetime = None
        self.last_result: Any = None
        self.run_count = 0
        self.error_count = 0

    @abstractmethod
    async def execute(self) -> Any:
        """
        Execute the task.

        Returns:
            Result of task execution
        """
        pass

    async def run(self) -> bool:
        """
        Run the task if it's time.

        Returns:
            True if task was executed, False if skipped
        """
        now = datetime.utcnow()

        if now < self.next_run:
            return False

        try:
            logger.info(f"Starting task: {self.name}")
            self.last_result = await self.execute()
            self.last_run = now
            self.next_run = now + timedelta(seconds=self.interval_seconds)
            self.run_count += 1
            logger.info(f"Task {self.name} completed successfully")
            return True
        except Exception as e:
            logger.error(f"Task {self.name} failed: {str(e)}", exc_info=True)
            self.error_count += 1
            self.next_run = now + timedelta(seconds=self.interval_seconds)
            return False

    def get_stats(self) -> Dict[str, Any]:
        """Get task statistics."""
        return {
            "name": self.name,
            "interval_seconds": self.interval_seconds,
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "next_run": self.next_run.isoformat(),
            "run_count": self.run_count,
            "error_count": self.error_count,
            "status": "due" if datetime.utcnow() >= self.next_run else "waiting",
        }


class TaskScheduler:
    """Manages and executes scheduled tasks."""

    def __init__(self):
        """Initialize the scheduler."""
        self.tasks: List[ScheduledTask] = []
        self.is_running = False

    def register_task(self, task: ScheduledTask) -> None:
        """
        Register a task to be scheduled.

        Args:
            task: Task to register
        """
        self.tasks.append(task)
        logger.info(f"Registered task: {task.name}")

    async def run_all(self) -> int:
        """
        Run all tasks that are due.

        Returns:
            Number of tasks executed
        """
        executed = 0
        for task in self.tasks:
            if await task.run():
                executed += 1
        return executed

    async def start(self, poll_interval: int = 60) -> None:
        """
        Start the scheduler loop.

        Args:
            poll_interval: Check interval in seconds
        """
        self.is_running = True
        logger.info("Scheduler started")

        try:
            while self.is_running:
                executed = await self.run_all()
                if executed > 0:
                    logger.debug(f"Executed {executed} scheduled tasks")
                await asyncio.sleep(poll_interval)
        except asyncio.CancelledError:
            logger.info("Scheduler stopped")
        except Exception as e:
            logger.error(f"Scheduler error: {str(e)}", exc_info=True)

    def stop(self) -> None:
        """Stop the scheduler."""
        self.is_running = False
        logger.info("Scheduler stop requested")

    def get_stats(self) -> Dict[str, Any]:
        """Get scheduler statistics."""
        return {
            "is_running": self.is_running,
            "task_count": len(self.tasks),
            "tasks": [task.get_stats() for task in self.tasks],
        }


# Budget alert task example
class BudgetAlertTask(ScheduledTask):
    """Task to check budget thresholds and create alerts."""

    def __init__(self, db_session=None, interval_seconds: int = 3600):
        """
        Initialize budget alert task.

        Args:
            db_session: Database session
            interval_seconds: Run interval (default: 1 hour)
        """
        super().__init__("budget_alerts", interval_seconds)
        self.db_session = db_session

    async def execute(self) -> Dict[str, Any]:
        """
        Check all user budgets and create alerts for exceeded thresholds.

        Returns:
            Dictionary with results
        """
        # This would be implemented with actual database queries
        # For now, it's a placeholder
        logger.debug("Checking budget thresholds...")

        result = {
            "checked_users": 0,
            "alerts_created": 0,
            "timestamp": datetime.utcnow().isoformat(),
        }

        if self.db_session:
            # TODO: Implement actual budget checking logic
            # from src.models.budget import Budget
            # from src.models.user import User
            #
            # users = self.db_session.query(User).all()
            # for user in users:
            #     # Check budgets and create alerts
            #     pass

            result["checked_users"] = 0  # Update with actual count
            result["alerts_created"] = 0  # Update with actual count

        return result


# Expense aggregation task example
class ExpenseAggregationTask(ScheduledTask):
    """Task to aggregate expenses for reporting and analytics."""

    def __init__(self, db_session=None, interval_seconds: int = 86400):
        """
        Initialize expense aggregation task.

        Args:
            db_session: Database session
            interval_seconds: Run interval (default: 24 hours)
        """
        super().__init__("expense_aggregation", interval_seconds)
        self.db_session = db_session

    async def execute(self) -> Dict[str, Any]:
        """
        Aggregate expenses for all users.

        Returns:
            Dictionary with results
        """
        logger.debug("Aggregating expenses...")

        result = {
            "aggregations_created": 0,
            "errors": 0,
            "timestamp": datetime.utcnow().isoformat(),
        }

        if self.db_session:
            # TODO: Implement actual aggregation logic
            pass

        return result


# Global scheduler instance
_scheduler: TaskScheduler = None


def get_scheduler() -> TaskScheduler:
    """Get or create the global scheduler."""
    global _scheduler
    if _scheduler is None:
        _scheduler = TaskScheduler()
    return _scheduler


def register_default_tasks(db_session=None) -> None:
    """
    Register default scheduled tasks.

    Args:
        db_session: Database session for tasks
    """
    scheduler = get_scheduler()

    # Register budget alert task (runs every 1 hour)
    budget_task = BudgetAlertTask(db_session=db_session, interval_seconds=3600)
    scheduler.register_task(budget_task)

    # Register expense aggregation task (runs daily at midnight)
    agg_task = ExpenseAggregationTask(db_session=db_session, interval_seconds=86400)
    scheduler.register_task(agg_task)

    logger.info("Default scheduled tasks registered")


async def start_scheduler(poll_interval: int = 60) -> None:
    """
    Start the scheduler in background.

    Args:
        poll_interval: Poll interval in seconds
    """
    scheduler = get_scheduler()
    await scheduler.start(poll_interval=poll_interval)


def stop_scheduler() -> None:
    """Stop the scheduler."""
    scheduler = get_scheduler()
    scheduler.stop()


def get_scheduler_stats() -> Dict[str, Any]:
    """Get scheduler statistics."""
    scheduler = get_scheduler()
    return scheduler.get_stats()
