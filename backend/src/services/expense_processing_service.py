"""
Service for processing expenses from various sources (OCR, text, etc.)
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from src.models.expense import Expense
from src.models.category import Category
from src.models.budget import Budget
from src.services.ocr_service import OCRService
from src.services.budget_management_service import BudgetManagementService
from src.services.financial_advice_service import FinancialAdviceService
from src.services.categorization_service import CategorizationService
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

    def extract_expense_from_text(
        self, text: str, user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Extract expense information from text input and auto-suggest category using LLM

        Args:
            text: Text containing expense information
            user_id: Optional user ID to enable LLM-based auto-categorization

        Returns:
            Dictionary with extracted expense data including optional category_id and confidence_score
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

            # Enhanced amount extraction for Vietnamese formats
            # Match patterns: 25k, 25K, 25,000đ, 25.000đ, 25000đ, 25000, $25, etc.
            amount_patterns = [
                r"(\d+(?:[,\.]\d{3})*)\s*(?:k|K)(?!\w)",  # 25k, 25.000k, 25,000K
                r"(\d+(?:[,\.]\d{3})*)\s*(?:đ|vnd|VND|₫)",  # 25,000đ, 25000đ
                r"\$\s*(\d+(?:[,\.]\d{3})*(?:\.\d{2})?)",  # $25, $25.00
                r"(\d{4,})\s*(?!\w)",  # 25000 (4+ digits without unit)
            ]

            for line in lines:
                lline = line.lower()
                # Look for amounts when context suggests money/purchase
                if any(
                    t in lline
                    for t in [
                        "$",
                        "cost",
                        "price",
                        "paid",
                        "spent",
                        "total",
                        "đ",
                        "vnd",
                        "k",
                        "mua",
                        "chi",
                        "trả",
                        "tiền",
                    ]
                ) or re.search(r"\d", line):
                    # Try each pattern
                    for pattern in amount_patterns:
                        matches = re.findall(pattern, line)
                        if matches:
                            try:
                                parsed = []
                                for match in matches:
                                    # Clean the matched string
                                    cleaned = match.replace(",", "").replace(".", "")
                                    if cleaned.isdigit():
                                        amount = float(cleaned)

                                        # Check if this is a "k" format in original line
                                        if re.search(
                                            rf"{re.escape(match)}\s*[kK](?!\w)", line
                                        ):
                                            amount *= 1000  # 25k = 25,000

                                        parsed.append(amount)

                                if parsed:
                                    expense_data["amount"] = parsed[0]
                                    if len(parsed) > 1:
                                        expense_data["amounts"] = parsed
                                    break  # Found amount, stop trying other patterns
                            except ValueError:
                                pass

                    if expense_data["amount"]:
                        break  # Found amount, stop processing lines

            if expense_data["amount"]:
                expense_data["confidence"] = 0.7

            # Extract merchant_name using LLM if not already extracted
            if not expense_data.get("merchant_name"):
                try:
                    merchant_name = self._extract_merchant_name_with_llm(text)
                    if merchant_name:
                        expense_data["merchant_name"] = merchant_name
                        logger.info(f"LLM extracted merchant_name: {merchant_name}")
                except Exception as e:
                    logger.warning(
                        f"LLM merchant extraction failed (non-blocking): {str(e)}"
                    )
                    # Continue without merchant_name

            # Auto-categorize if user_id provided
            # Priority: 1. Keyword rules (learned from user) 2. LLM
            if user_id and (
                expense_data.get("merchant_name") or expense_data.get("description") or text
            ):
                try:
                    # FIRST: Try keyword rules (includes learned rules from user corrections)
                    # This is prioritized because user-learned rules are more accurate
                    categorized_by_rules = self._categorize_with_keywords(
                        user_id, expense_data, original_text=text
                    )
                    
                    if categorized_by_rules:
                        logger.info(
                            f"Categorized by keyword rules: {expense_data.get('category_id')}"
                        )
                    else:
                        # SECOND: Fallback to LLM if no rules match
                        merchant_or_desc = expense_data.get(
                            "merchant_name"
                        ) or expense_data.get("description", "")
                        logger.info(
                            f"No keyword rules matched, attempting LLM categorization for '{merchant_or_desc}'"
                        )

                        if self.db_session:
                            from src.services.ai_agent_service import AIAgentService

                            ai_service = AIAgentService(self.db_session)
                            category_id, confidence = (
                                ai_service.categorize_expense_with_llm(
                                    user_id=user_id,
                                    merchant_name=expense_data.get("merchant_name") or "",
                                    description=expense_data.get("description") or text,
                                    amount=expense_data.get("amount", 0),
                                )
                            )

                            if category_id:
                                expense_data["category_id"] = category_id
                                expense_data["suggested_category_id"] = category_id
                                expense_data["categorization_confidence"] = (
                                    confidence or 0.8
                                )
                                logger.info(
                                    f"LLM categorized expense to {category_id} with confidence {confidence}"
                                )

                except Exception as e:
                    # Don't fail extraction if categorization fails
                    logger.warning(
                        f"Auto-categorization failed (non-blocking): {str(e)}"
                    )

            return expense_data

        except Exception as e:
            logger.error(f"Error extracting expense from text: {str(e)}")
            raise ValidationError(f"Failed to extract expense from text: {str(e)}")

    def _extract_merchant_name_with_llm(self, text: str) -> Optional[str]:
        """
        Extract merchant/store name from text using LLM

        Args:
            text: Text containing expense information

        Returns:
            Merchant name if found, None otherwise
        """
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            from langchain_core.messages import HumanMessage

            # Use lite model for lightweight extraction
            lite_model = ChatGoogleGenerativeAI(
                model="gemini-2.5-flash-lite", temperature=0.1
            )

            extraction_prompt = f"""Bạn là một chuyên gia trích xuất thông tin chi tiêu. Từ đoạn text sau, hãy trích xuất tên cửa hàng/nơi mua hàng (merchant/store name).

Text: "{text}"

**Yêu cầu:**
1. Trích xuất tên cửa hàng, cửa tiệm, nhà hàng, hoặc địa điểm mua hàng
2. KHÔNG trích xuất tên món ăn, đồ uống, hoặc sản phẩm (ví dụ: "cà phê", "phở", "bánh mì" là sản phẩm, không phải cửa hàng)
3. Nếu có từ khóa chỉ địa điểm như "ở", "tại", "từ" thì tên cửa hàng thường nằm sau các từ này
4. Tên cửa hàng thường là tên riêng hoặc tên thương hiệu (ví dụ: "Highlands Coffee", "Circle K", "VinMart", "Grab")
5. Nếu không tìm thấy tên cửa hàng rõ ràng, trả về null

**Ví dụ:**
- "Tôi vừa mua cà phê ở Highlands Coffee 25k" → "Highlands Coffee"
- "Ăn phở tại Phở 24 50,000đ" → "Phở 24"
- "Mua nước ở Circle K 15k" → "Circle K"
- "Chi Grab 30k" → "Grab"
- "Mua cà phê 25k" → null (không có tên cửa hàng)
- "Tôi vừa mua bánh mì 20k" → null (không có tên cửa hàng)

Trả về JSON format (không markdown):
{{
  "merchant_name": "Tên cửa hàng hoặc null",
  "confidence": 0.0-1.0
}}

Chỉ trả về JSON, không có markdown."""

            response = lite_model.invoke([HumanMessage(content=extraction_prompt)])
            response_text = response.content.strip()

            logger.debug(f"LLM merchant extraction response: {response_text}")

            # Parse JSON response
            try:
                # Clean up markdown if present
                if "```json" in response_text:
                    response_text = (
                        response_text.split("```json")[1].split("```")[0].strip()
                    )
                elif "```" in response_text:
                    response_text = (
                        response_text.split("```")[1].split("```")[0].strip()
                    )

                result = json.loads(response_text)
                merchant_name = result.get("merchant_name")

                # Return None if merchant_name is null, empty, or "null" string
                if not merchant_name or merchant_name.lower() == "null":
                    return None

                # Clean and return merchant name
                merchant_name = merchant_name.strip()
                if len(merchant_name) > 1:
                    return merchant_name.title()
                return None

            except json.JSONDecodeError as e:
                logger.error(
                    f"Failed to parse LLM merchant extraction response: {str(e)}"
                )
                logger.error(f"Response was: {response_text}")
                return None

        except Exception as e:
            logger.warning(f"Error extracting merchant name with LLM: {str(e)}")
            return None

    def _categorize_with_keywords(
        self, user_id: str, expense_data: Dict[str, Any], original_text: str = ""
    ) -> bool:
        """
        Categorization using keyword rules (includes user-learned rules)
        
        Priority order for matching:
        1. merchant_name
        2. description  
        3. original_text (user's input)

        Args:
            user_id: User ID
            expense_data: Expense data dictionary to update with category
            original_text: Original user input text
            
        Returns:
            True if categorization was successful, False otherwise
        """
        try:
            if not self.db_session:
                return False

            # Build list of texts to try matching
            texts_to_match = []
            if expense_data.get("merchant_name"):
                texts_to_match.append(expense_data.get("merchant_name"))
            if expense_data.get("description"):
                texts_to_match.append(expense_data.get("description"))
            if original_text:
                texts_to_match.append(original_text)
                
            if not texts_to_match:
                return False

            logger.info(
                f"Checking keyword rules for texts: {texts_to_match}"
            )

            categorization_service = CategorizationService()

            # Get user's categorization rules
            from src.models.expense_categorization_rule import (
                ExpenseCategorizationRule,
            )

            rules = (
                self.db_session.query(ExpenseCategorizationRule)
                .filter(
                    ExpenseCategorizationRule.user_id == user_id,
                    ExpenseCategorizationRule.is_active == True,
                )
                .all()
            )

            if not rules:
                logger.debug(f"No categorization rules found for user {user_id}")
                return False

            # Try to match rules against all text sources
            best_match = None
            best_confidence = 0.0

            for rule in rules:
                for text in texts_to_match:
                    if not text:
                        continue
                    confidence = categorization_service._match_rule_for_text(text, rule)
                    if confidence > best_confidence:
                        best_confidence = confidence
                        best_match = rule

            # If we found a good match, add category suggestion
            if best_match and best_confidence >= best_match.confidence_threshold:
                expense_data["category_id"] = best_match.category_id
                expense_data["suggested_category_id"] = best_match.category_id
                expense_data["categorization_confidence"] = best_confidence
                logger.info(
                    f"Keyword rule matched: '{best_match.store_name_pattern}' -> category {best_match.category_id} (confidence: {best_confidence})"
                )
                return True
            
            return False

        except Exception as e:
            logger.warning(
                f"Keyword categorization failed (non-blocking): {str(e)}"
            )
            return False

    def extract_expense_from_image(
        self, image_data, user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Extract expense information from invoice image using OCR and auto-categorize using LLM

        Args:
            image_data: Image file data
            user_id: Optional user ID to enable LLM-based auto-categorization

        Returns:
            Dictionary with extracted expense data including optional category_id and confidence_score
        """
        try:
            logger.info("Extracting expense from image using OCR")

            ocr_result = self.ocr_service.process_invoice(image_data)

            expense_data = {
                "merchant_name": ocr_result.get("store_name"),
                "amount": ocr_result.get("total_amount", 0),
                "date": ocr_result.get("date"),
                "confidence": 0.9,  # OCR usually has high confidence
                "description": "Extracted from invoice image",
            }

            # Auto-categorize using LLM if user_id provided (similar to extract_expense_from_text)
            if user_id and (
                expense_data.get("merchant_name") or expense_data.get("description")
            ):
                try:
                    merchant_or_desc = expense_data.get(
                        "merchant_name"
                    ) or expense_data.get("description", "")
                    logger.info(
                        f"Attempting to categorize expense from image (merchant: '{merchant_or_desc}') using LLM for user {user_id}"
                    )

                    # Import AIAgentService to use LLM categorization
                    if self.db_session:
                        from src.services.ai_agent_service import AIAgentService

                        ai_service = AIAgentService(self.db_session)
                        category_id, confidence = (
                            ai_service.categorize_expense_with_llm(
                                user_id=user_id,
                                merchant_name=expense_data.get("merchant_name") or "",
                                description=expense_data.get("description")
                                or "Extracted from invoice image",
                                amount=expense_data.get("amount", 0),
                            )
                        )

                        if category_id:
                            expense_data["category_id"] = category_id
                            expense_data["suggested_category_id"] = category_id
                            expense_data["categorization_confidence"] = (
                                confidence or 0.8
                            )
                            logger.info(
                                f"LLM categorized expense from image to {category_id} with confidence {confidence}"
                            )
                        else:
                            # Fallback to keyword rules if LLM fails
                            logger.warning(
                                "LLM categorization returned None, falling back to keyword rules"
                            )
                            self._categorize_with_keywords(user_id, expense_data)
                    else:
                        logger.warning("No DB session available for LLM categorization")
                        self._categorize_with_keywords(user_id, expense_data)

                except Exception as e:
                    # Don't fail extraction if categorization fails
                    logger.warning(
                        f"Auto-categorization failed (non-blocking): {str(e)}"
                    )
                    # Fallback to keyword rules
                    self._categorize_with_keywords(user_id, expense_data)

            return expense_data

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

            # Handle date - default to current date if not provided
            expense_date = None
            date_value = expense_data.get("date")
            if date_value and date_value not in ["Hôm nay", "hôm nay", None, ""]:
                try:
                    expense_date = datetime.fromisoformat(date_value)
                except (ValueError, TypeError):
                    # If date parsing fails, use current date
                    expense_date = datetime.utcnow()
            else:
                # Default to current date
                expense_date = datetime.utcnow()

            # Create expense record
            expense = Expense(
                user_id=user_id,
                merchant_name=expense_data.get("merchant_name"),
                amount=expense_data.get("amount"),
                date=expense_date,
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
                            "description": description,
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

        Now uses CategoryLearningService to automatically create categorization rules
        when a user corrects a category assignment.

        Args:
            expense_id: Expense ID
            user_id: User ID
            correction_records: List of correction records
        """
        try:
            from src.models.categorization_feedback import CategorizationFeedback
            from src.services.category_learning_service import CategoryLearningService

            # Get the expense to access its category
            expense = self.db_session.query(Expense).filter_by(id=expense_id).first()
            if not expense:
                logger.warning(f"Expense {expense_id} not found for learning storage")
                return

            # Check if category was corrected
            category_correction = None
            original_category_id = None
            for record in correction_records:
                if record.get("field") == "category_id":
                    category_correction = record
                    original_category_id = record.get("old_value")
                    break

            # If category was corrected, use CategoryLearningService for auto-learning
            if category_correction and expense.category_id:
                try:
                    learning_service = CategoryLearningService(self.db_session)
                    learning_result = learning_service.learn_from_correction(
                        user_id=user_id,
                        expense_id=expense_id,
                        corrected_category_id=expense.category_id,
                        original_category_id=original_category_id,
                    )
                    logger.info(
                        f"Auto-learned from category correction: {learning_result.get('message', 'Success')}"
                    )
                except Exception as learning_error:
                    logger.warning(
                        f"Category learning failed (non-blocking): {str(learning_error)}"
                    )

            # Store feedback for corrections (existing behavior)
            if expense.category_id:
                feedback = CategorizationFeedback(
                    expense_id=expense_id,
                    user_id=user_id,
                    feedback_type="correction",
                    suggested_category_id=original_category_id or expense.category_id,
                    confirmed_category_id=expense.category_id,
                    confidence_score=0.0,
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
