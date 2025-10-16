"""
Service for processing expenses from various sources (OCR, text, etc.)
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from src.models.expense import Expense
from src.models.expense_category import ExpenseCategory
from src.models.budget import Budget
from src.services.ocr_service import OCRService
from src.services.budget_management_service import BudgetManagementService
from src.services.financial_advice_service import FinancialAdviceService
from src.utils.validators import validate_amount, validate_date_string
from src.utils.exceptions import ValidationError


logger = logging.getLogger(__name__)


class ExpenseProcessingService:
    """
    Service for processing expenses extracted from various sources
    """

    def __init__(self, db_session: Optional[Session] = None):
        self.db_session = db_session
        self.ocr_service = OCRService()
        self.budget_service = BudgetManagementService(db_session)
        self.advice_service = FinancialAdviceService()

    def extract_expense_from_text(self, text: str) -> Dict[str, Any]:
        """
        Extract expense information from text input

        Args:
            text: Text containing expense information

        Returns:
            Dictionary with extracted expense data
        """
        try:
            logger.info("Extracting expense from text")

            # Parse text to extract expense details (lightweight path)
            original_text = text
            lower_text = text.lower()
            lines = original_text.split("\n")
            expense_data = {
                "merchant_name": None,
                "amount": None,
                "date": None,
                "confidence": 0.5,
                "description": text,
            }

            import re
            for line in lines:
                lline = line.lower()
                # Look for amounts when context suggests a purchase
                if any(t in lline for t in ["$", "cost", "price", "paid", "spent", "total"]):
                    amounts = re.findall(r"\$?[\d,]+\.?\d*", line)
                    if amounts:
                        try:
                            parsed = [
                                float(a.replace("$", "").replace(",", ""))
                                for a in amounts
                            ]
                            expense_data["amount"] = parsed[0]
                            if len(parsed) > 1:
                                # Phase 6: signal multiple amounts to caller
                                expense_data["amounts"] = parsed
                        except ValueError:
                            pass

                # Look for merchant after keywords like 'at '
                m = re.search(r"\bat\s+([A-Z][A-Za-z0-9&\-\s]{1,40})", line)
                if m and not expense_data.get("merchant_name"):
                    merchant_guess = m.group(1).strip()
                    # Trim trailing generic words
                    merchant_guess = re.sub(r"\s+(yesterday|today|tonight)$", "", merchant_guess, flags=re.I)
                    expense_data["merchant_name"] = merchant_guess

            if expense_data["amount"]:
                expense_data["confidence"] = 0.7

            return expense_data

        except Exception as e:
            logger.error(f"Error extracting expense from text: {str(e)}")
            raise ValidationError(f"Failed to extract expense from text: {str(e)}")

    def extract_expense_from_image(self, image_data) -> Dict[str, Any]:
        """
        Extract expense information from invoice image using OCR

        Args:
            image_data: Image file data

        Returns:
            Dictionary with extracted expense data
        """
        try:
            logger.info("Extracting expense from image using OCR")

            ocr_result = self.ocr_service.process_invoice(image_data)

            return {
                "merchant_name": ocr_result.get("store_name"),
                "amount": ocr_result.get("total_amount", 0),
                "date": ocr_result.get("date"),
                "confidence": 0.9,  # OCR usually has high confidence
                "description": "Extracted from invoice image",
            }

        except Exception as e:
            logger.error(f"Error extracting expense from image: {str(e)}")
            raise ValidationError(f"Failed to extract expense from image: {str(e)}")

    def validate_extracted_expense(self, expense_data: Dict[str, Any]) -> bool:
        """
        Validate extracted expense data

        Args:
            expense_data: Dictionary with expense data

        Returns:
            True if valid, False otherwise
        """
        try:
            # Validate amount
            if not expense_data.get("amount"):
                return False

            validate_amount(expense_data["amount"], "Expense amount")

            # Validate date if provided
            if expense_data.get("date"):
                validate_date_string(expense_data["date"])
                # Phase 6: reject future dates
                try:
                    from datetime import datetime as _dt
                    dt = _dt.fromisoformat(expense_data["date"]).date()
                    if dt > _dt.utcnow().date():
                        return False
                except Exception:
                    return False

            return True

        except Exception as e:
            logger.warning(f"Expense validation failed: {str(e)}")
            return False

    def save_expense(
        self,
        user_id: str,
        expense_data: Dict[str, Any],
        category_id: Optional[str] = None,
        source_type: str = "text",
    ) -> Tuple[Expense, Optional[Dict[str, Any]]]:
        """
        Save expense to database and check for budget warnings

        Args:
            user_id: User ID
            expense_data: Dictionary with expense data
            category_id: Optional category ID
            source_type: Type of source ('text' or 'image')

        Returns:
            Tuple of (Expense object, budget warning dictionary or None)
        """
        try:
            if not self.db_session:
                raise ValueError("Database session not available")

            # Create expense record
            expense = Expense(
                user_id=user_id,
                merchant_name=expense_data.get("merchant_name"),
                amount=expense_data.get("amount"),
                date=(
                    datetime.fromisoformat(expense_data["date"])
                    if expense_data.get("date")
                    else None
                ),
                category_id=category_id,
                description=expense_data.get("description"),
                confirmed_by_user=False,
                source_type=source_type,
                source_metadata=json.dumps(
                    {
                        "confidence": expense_data.get("confidence", 0),
                        "original_data": expense_data,
                    }
                ),
            )

            self.db_session.add(expense)
            self.db_session.commit()
            self.db_session.refresh(expense)

            logger.info(f"Expense saved with ID: {expense.id}")

            # Check for budget warnings
            budget_warning = None
            if category_id:
                budget_info = self.budget_service.check_budget_status(
                    user_id=user_id,
                    category_id=category_id,
                    amount=expense_data.get("amount"),
                )

                if budget_info and budget_info.get("warning"):
                    budget_warning = {
                        "category": budget_info.get("category_name"),
                        "limit": budget_info.get("limit"),
                        "spent": budget_info.get("spent"),
                        "remaining": budget_info.get("remaining"),
                        "alert_level": budget_info.get("alert_level"),
                        "message": budget_info.get("message"),
                    }

            return expense, budget_warning

        except Exception as e:
            logger.error(f"Error saving expense: {str(e)}")
            if self.db_session:
                self.db_session.rollback()
            raise

    def confirm_expense(
        self, expense_id: str, corrections: Optional[Dict[str, Any]] = None
    ) -> Expense:
        """
        Confirm an expense and apply any corrections

        Args:
            expense_id: Expense ID
            corrections: Optional corrections to apply

        Returns:
            Updated Expense object
        """
        try:
            if not self.db_session:
                raise ValueError("Database session not available")

            expense = self.db_session.query(Expense).filter_by(id=expense_id).first()
            if not expense:
                raise ValidationError(f"Expense not found: {expense_id}")

            # Apply corrections if provided
            if corrections:
                if "merchant_name" in corrections:
                    expense.merchant_name = corrections["merchant_name"]
                if "amount" in corrections:
                    validate_amount(corrections["amount"], "Corrected amount")
                    expense.amount = corrections["amount"]
                if "date" in corrections:
                    validate_date_string(corrections["date"])
                    expense.date = datetime.fromisoformat(corrections["date"])

            expense.confirmed_by_user = True
            self.db_session.commit()
            self.db_session.refresh(expense)

            logger.info(f"Expense confirmed with ID: {expense_id}")
            return expense

        except Exception as e:
            logger.error(f"Error confirming expense: {str(e)}")
            if self.db_session:
                self.db_session.rollback()
            raise

    def get_expense(self, expense_id: str) -> Expense:
        """
        Get an expense by ID

        Args:
            expense_id: Expense ID

        Returns:
            Expense object
        """
        if not self.db_session:
            raise ValueError("Database session not available")

        expense = self.db_session.query(Expense).filter_by(id=expense_id).first()
        if not expense:
            raise ValidationError(f"Expense not found: {expense_id}")

        return expense

    def update_expense(
        self,
        expense_id: str,
        user_id: str,
        corrections: Dict[str, Any],
        store_learning: bool = True,
        return_budget_warning: bool = False,
    ) -> Tuple[Expense, Optional[Dict[str, Any]]]:
        """
        Update an expense with user corrections (User Story 2)

        Args:
            expense_id: Expense ID to update
            user_id: User ID making the correction
            corrections: Dictionary of field corrections
            store_learning: Whether to store corrections for future learning
            return_budget_warning: Whether to return updated budget warning

        Returns:
            Tuple of (Updated Expense object, optional budget warning)
        """
        try:
            if not self.db_session:
                raise ValueError("Database session not available")

            # Get the expense
            expense = self.db_session.query(Expense).filter_by(id=expense_id).first()
            if not expense:
                raise ValidationError(f"Expense not found: {expense_id}")

            # Verify ownership
            if expense.user_id != user_id:
                raise ValidationError(
                    "Unauthorized: Cannot update another user's expense"
                )

            # Store original values for learning
            original_values = {
                "merchant_name": expense.merchant_name,
                "amount": expense.amount,
                "date": expense.date,
            }

            # Apply corrections with validation
            correction_records = []

            if "merchant_name" in corrections:
                if corrections["merchant_name"] != expense.merchant_name:
                    correction_records.append(
                        {
                            "field": "merchant_name",
                            "old_value": expense.merchant_name,
                            "new_value": corrections["merchant_name"],
                            "timestamp": datetime.utcnow().isoformat(),
                        }
                    )
                    expense.merchant_name = corrections["merchant_name"]

            if "amount" in corrections:
                validate_amount(corrections["amount"], "Corrected amount")
                if corrections["amount"] != expense.amount:
                    correction_records.append(
                        {
                            "field": "amount",
                            "old_value": float(expense.amount),
                            "new_value": float(corrections["amount"]),
                            "timestamp": datetime.utcnow().isoformat(),
                        }
                    )
                    expense.amount = corrections["amount"]

            if "date" in corrections:
                date_str = corrections["date"]
                if isinstance(date_str, str):
                    validate_date_string(date_str)
                    new_date = datetime.fromisoformat(date_str)
                else:
                    new_date = date_str

                if new_date != expense.date:
                    correction_records.append(
                        {
                            "field": "date",
                            "old_value": (
                                expense.date.isoformat() if expense.date else None
                            ),
                            "new_value": new_date.isoformat(),
                            "timestamp": datetime.utcnow().isoformat(),
                        }
                    )
                    expense.date = new_date

            if "category_id" in corrections:
                if corrections["category_id"] != expense.category_id:
                    correction_records.append(
                        {
                            "field": "category_id",
                            "old_value": expense.category_id,
                            "new_value": corrections["category_id"],
                            "timestamp": datetime.utcnow().isoformat(),
                        }
                    )
                    expense.category_id = corrections["category_id"]

            # Mark as confirmed by user
            expense.confirmed_by_user = True

            # Update metadata to include correction history
            if expense.source_metadata:
                try:
                    metadata = json.loads(expense.source_metadata)
                except (json.JSONDecodeError, TypeError):
                    metadata = {}
            else:
                metadata = {}

            if "correction_history" not in metadata:
                metadata["correction_history"] = []

            metadata["correction_history"].extend(correction_records)
            expense.source_metadata = json.dumps(metadata)

            self.db_session.commit()
            self.db_session.refresh(expense)

            logger.info(
                f"Expense {expense_id} updated with {len(correction_records)} corrections"
            )

            # Store learning if requested
            if store_learning and correction_records:
                self._store_correction_learning(
                    expense_id=expense.id,
                    user_id=user_id,
                    correction_records=correction_records,
                )

            # Calculate budget warning if requested
            budget_warning = None
            if return_budget_warning and expense.category_id:
                budget_info = self.budget_service.check_budget_status(
                    user_id=user_id,
                    category_id=expense.category_id,
                    amount=expense.amount,
                )

                if budget_info and budget_info.get("warning"):
                    budget_warning = {
                        "category": budget_info.get("category_name"),
                        "limit": budget_info.get("limit"),
                        "spent": budget_info.get("spent"),
                        "remaining": budget_info.get("remaining"),
                        "alert_level": budget_info.get("alert_level"),
                        "message": budget_info.get("message"),
                    }

            return expense, budget_warning

        except ValidationError:
            if self.db_session:
                self.db_session.rollback()
            raise
        except Exception as e:
            logger.error(f"Error updating expense: {str(e)}")
            if self.db_session:
                self.db_session.rollback()
            raise ValidationError(f"Failed to update expense: {str(e)}")

    def get_correction_history(self, expense_id: str) -> list:
        """
        Get correction history for an expense

        Args:
            expense_id: Expense ID

        Returns:
            List of correction records
        """
        try:
            expense = self.get_expense(expense_id)

            if not expense.source_metadata:
                return []

            try:
                metadata = json.loads(expense.source_metadata)
                return metadata.get("correction_history", [])
            except (json.JSONDecodeError, TypeError):
                return []

        except Exception as e:
            logger.error(f"Error retrieving correction history: {str(e)}")
            return []

    def create_expense(
        self,
        user_id: str,
        merchant_name: Optional[str] = None,
        amount: float = 0.0,
        date: Optional[str] = None,
        category_id: Optional[str] = None,
        description: Optional[str] = None,
        source_type: str = "manual",
    ) -> Expense:
        """
        Create a new expense record

        Args:
            user_id: User ID
            merchant_name: Name of merchant/store
            amount: Expense amount
            date: Expense date (YYYY-MM-DD)
            category_id: Category ID
            description: Description of expense
            source_type: Type of source (default: 'manual')

        Returns:
            Created Expense object
        """
        try:
            if not self.db_session:
                raise ValueError("Database session not available")
            
            # Validate amount
            if amount <= 0:
                raise ValidationError("Amount must be greater than 0")
            
            # Validate date if provided
            if date:
                validate_date_string(date)
                # Phase 6: reject future dates
                try:
                    from datetime import datetime as _dt
                    dt = _dt.fromisoformat(date).date()
                    if dt > _dt.utcnow().date():
                        raise ValidationError("Date cannot be in the future")
                except Exception:
                    raise ValidationError("Invalid date format")
            
            # Create expense record
            expense = Expense(
                user_id=user_id,
                merchant_name=merchant_name,
                amount=amount,
                date=datetime.fromisoformat(date) if date else None,
                category_id=category_id,
                description=description,
                confirmed_by_user=True,  # Manual entries are considered confirmed
                source_type=source_type,
                source_metadata=json.dumps(
                    {
                        "confidence": 1.0,  # Manual entries have full confidence
                        "original_data": {
                            "merchant_name": merchant_name,
                            "amount": amount,
                            "date": date,
                            "category_id": category_id,
                            "description": description
                        },
                    }
                ),
            )

            self.db_session.add(expense)
            self.db_session.commit()
            self.db_session.refresh(expense)

            logger.info(f"Expense created with ID: {expense.id}")

            return expense

        except ValidationError:
            if self.db_session:
                self.db_session.rollback()
            raise
        except Exception as e:
            logger.error(f"Error creating expense: {str(e)}")
            if self.db_session:
                self.db_session.rollback()
            raise ValidationError(f"Failed to create expense: {str(e)}")


    def _store_correction_learning(
        self,
        expense_id: str,
        user_id: str,
        correction_records: list,
    ) -> None:
        """
        Store corrections for future learning (User Story 2 requirement)

        Args:
            expense_id: Expense ID
            user_id: User ID
            correction_records: List of correction records
        """
        try:
            from src.models.categorization_feedback import CategorizationFeedback

            # Get the expense to access its category
            expense = self.db_session.query(Expense).filter_by(id=expense_id).first()
            if not expense:
                logger.warning(f"Expense {expense_id} not found for learning storage")
                return

            # Store feedback for corrections
            # Note: The current CategorizationFeedback model is designed for category feedback
            # For now, we'll store corrections using the existing model structure
            # Future enhancement: Create a dedicated ExpenseCorrection model

            if expense.category_id:
                feedback = CategorizationFeedback(
                    expense_id=expense_id,
                    user_id=user_id,
                    feedback_type="correction",
                    suggested_category_id=expense.category_id,  # Use current category
                    confirmed_category_id=expense.category_id,  # Same after correction
                    confidence_score=0.0,  # Will be enhanced in future
                )
                self.db_session.add(feedback)
                self.db_session.commit()
                logger.info(
                    f"Stored correction learning record for expense {expense_id}"
                )
            else:
                logger.info(
                    f"No category for expense {expense_id}, skipping learning storage"
                )

        except Exception as e:
            logger.warning(f"Failed to store correction learning: {str(e)}")
            # Don't fail the whole operation if learning storage fails
            if self.db_session:
                self.db_session.rollback()
