"""
Category Learning Service - Auto-learn from user corrections

This service enables the AI agent to learn from user corrections on expense categorization.
When a user corrects a category, the system automatically:
1. Extracts keywords from the expense description
2. Creates new categorization rules for future auto-categorization
3. Uses feedback history to improve suggestions
"""

import logging
import re
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func
from src.models.expense import Expense
from src.models.category import Category
from src.models.expense_categorization_rule import ExpenseCategorizationRule
from src.models.categorization_feedback import CategorizationFeedback


logger = logging.getLogger(__name__)


class CategoryLearningServiceError(Exception):
    """Custom exception for category learning service errors"""

    pass


# Vietnamese stopwords to exclude from keyword extraction
VIETNAMESE_STOPWORDS = {
    "của", "và", "là", "để", "cho", "với", "trong", "này", "đó", "có",
    "được", "một", "các", "những", "từ", "đến", "theo", "về", "như",
    "trên", "dưới", "sau", "trước", "khi", "nếu", "vì", "nhưng",
    "hoặc", "hay", "rồi", "vậy", "thì", "mà", "bị", "ra", "vào",
    "lên", "xuống", "đi", "đến", "vừa", "mới", "đã", "sẽ", "đang",
    "còn", "nữa", "quá", "rất", "lắm", "cũng", "chỉ", "tất", "cả",
    "k", "vnd", "đ", "vnđ", "đồng", "nghìn", "triệu", "tỷ",
}

# Common amount patterns to exclude
AMOUNT_PATTERNS = [
    r"\d+k",  # 25k, 100k
    r"\d+đ",  # 25đ
    r"\d+\.?\d*\s*(vnđ|vnd|đồng|nghìn|triệu)",  # 25000 vnd
    r"\d+",  # Pure numbers
]


class CategoryLearningService:
    """
    Service for learning from user corrections to improve categorization
    """

    def __init__(self, db_session: Session = None):
        self.db_session = db_session

    def extract_keywords_from_text(
        self, text: str, min_length: int = 2
    ) -> List[str]:
        """
        Extract meaningful keywords from expense description/merchant name

        Args:
            text: Text to extract keywords from
            min_length: Minimum length of keyword

        Returns:
            List of extracted keywords
        """
        if not text:
            return []

        # Convert to lowercase
        text = text.lower().strip()

        # Remove amount patterns
        for pattern in AMOUNT_PATTERNS:
            text = re.sub(pattern, "", text, flags=re.IGNORECASE)

        # Split by non-word characters (keep Vietnamese characters)
        words = re.findall(r"[\w\u00C0-\u024F\u1E00-\u1EFF]+", text)

        # Filter out stopwords and short words
        keywords = [
            word
            for word in words
            if word not in VIETNAMESE_STOPWORDS
            and len(word) >= min_length
            and not word.isdigit()
        ]

        # Remove duplicates while preserving order
        seen = set()
        unique_keywords = []
        for kw in keywords:
            if kw not in seen:
                seen.add(kw)
                unique_keywords.append(kw)

        return unique_keywords

    def learn_from_correction(
        self,
        user_id: str,
        expense_id: str,
        corrected_category_id: str,
        original_category_id: Optional[str] = None,
        confidence_threshold: float = 0.85,
    ) -> Dict[str, Any]:
        """
        Learn from a category correction and create new rules automatically

        Args:
            user_id: User ID
            expense_id: Expense ID that was corrected
            corrected_category_id: The correct category selected by user
            original_category_id: Original suggested category (if any)
            confidence_threshold: Confidence threshold for the new rule

        Returns:
            Dictionary containing learning results (rules created, keywords learned)
        """
        try:
            if not self.db_session:
                raise CategoryLearningServiceError("Database session required")

            logger.info(
                f"Learning from correction for expense {expense_id}, "
                f"corrected to category {corrected_category_id}"
            )

            # Get the expense
            expense = (
                self.db_session.query(Expense)
                .filter(Expense.id == expense_id)
                .first()
            )

            if not expense:
                raise CategoryLearningServiceError(f"Expense {expense_id} not found")

            # Verify category exists and belongs to user
            category = (
                self.db_session.query(Category)
                .filter(
                    Category.id == corrected_category_id,
                    Category.user_id == user_id,
                )
                .first()
            )

            if not category:
                raise CategoryLearningServiceError(
                    f"Category {corrected_category_id} not found"
                )

            # Extract keywords from expense
            text_sources = []
            if expense.description:
                text_sources.append(expense.description)
            if expense.merchant_name:
                text_sources.append(expense.merchant_name)

            combined_text = " ".join(text_sources)
            keywords = self.extract_keywords_from_text(combined_text)

            if not keywords:
                logger.info(f"No keywords extracted from expense {expense_id}")
                return {
                    "expense_id": expense_id,
                    "category_id": corrected_category_id,
                    "keywords_learned": [],
                    "rules_created": 0,
                    "message": "No keywords to learn from",
                }

            rules_created = []
            keywords_learned = []

            for keyword in keywords:
                # Check if rule already exists for this keyword and category
                existing_rule = (
                    self.db_session.query(ExpenseCategorizationRule)
                    .filter(
                        ExpenseCategorizationRule.user_id == user_id,
                        ExpenseCategorizationRule.category_id == corrected_category_id,
                        func.lower(ExpenseCategorizationRule.store_name_pattern)
                        == keyword.lower(),
                    )
                    .first()
                )

                if existing_rule:
                    # Rule exists, boost its confidence if it's lower
                    if existing_rule.confidence_threshold < confidence_threshold:
                        existing_rule.confidence_threshold = min(
                            confidence_threshold + 0.05, 0.99
                        )
                        logger.info(
                            f"Boosted confidence for existing rule: {keyword} -> {category.name}"
                        )
                    keywords_learned.append(keyword)
                    continue

                # Check if this keyword maps to a DIFFERENT category
                conflicting_rule = (
                    self.db_session.query(ExpenseCategorizationRule)
                    .filter(
                        ExpenseCategorizationRule.user_id == user_id,
                        func.lower(ExpenseCategorizationRule.store_name_pattern)
                        == keyword.lower(),
                        ExpenseCategorizationRule.category_id != corrected_category_id,
                    )
                    .first()
                )

                if conflicting_rule:
                    # User is correcting a previous categorization
                    # Update the existing rule to point to the new category
                    old_category_id = conflicting_rule.category_id
                    conflicting_rule.category_id = corrected_category_id
                    conflicting_rule.confidence_threshold = confidence_threshold
                    logger.info(
                        f"Updated conflicting rule: {keyword} from category "
                        f"{old_category_id} to {corrected_category_id}"
                    )
                    keywords_learned.append(keyword)
                    rules_created.append(
                        {
                            "keyword": keyword,
                            "category": category.name,
                            "action": "updated",
                        }
                    )
                    continue

                # Create new rule
                new_rule = ExpenseCategorizationRule(
                    user_id=user_id,
                    category_id=corrected_category_id,
                    store_name_pattern=keyword,
                    rule_type="keyword",
                    confidence_threshold=confidence_threshold,
                    is_active=True,
                )
                self.db_session.add(new_rule)
                keywords_learned.append(keyword)
                rules_created.append(
                    {
                        "keyword": keyword,
                        "category": category.name,
                        "action": "created",
                    }
                )
                logger.info(f"Created new rule: {keyword} -> {category.name}")

            self.db_session.commit()

            result = {
                "expense_id": expense_id,
                "category_id": corrected_category_id,
                "category_name": category.name,
                "keywords_learned": keywords_learned,
                "rules_created": len(rules_created),
                "rules_details": rules_created,
                "message": f"Learned {len(keywords_learned)} keywords for category '{category.name}'",
            }

            logger.info(f"Learning complete: {result}")
            return result

        except CategoryLearningServiceError:
            raise
        except Exception as e:
            logger.error(f"Error learning from correction: {str(e)}")
            if self.db_session:
                self.db_session.rollback()
            raise CategoryLearningServiceError(f"Error learning from correction: {str(e)}")

    def get_suggestion_from_history(
        self,
        user_id: str,
        text: str,
        db_session: Session = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Get category suggestion based on similar past corrections

        Args:
            user_id: User ID
            text: Text to match (description or merchant name)
            db_session: Database session (optional, uses self.db_session if not provided)

        Returns:
            Dictionary with suggested category or None
        """
        try:
            session = db_session or self.db_session
            if not session:
                return None

            # Extract keywords from the input text
            keywords = self.extract_keywords_from_text(text)

            if not keywords:
                return None

            # Find feedback records where the expense had similar keywords
            # and the user made a correction
            best_match = None
            best_score = 0

            for keyword in keywords:
                # Query expenses with this keyword that have been corrected
                feedbacks = (
                    session.query(CategorizationFeedback)
                    .join(Expense, CategorizationFeedback.expense_id == Expense.id)
                    .filter(
                        CategorizationFeedback.user_id == user_id,
                        CategorizationFeedback.feedback_type == "correction",
                        func.lower(Expense.description).contains(keyword.lower())
                        | func.lower(Expense.merchant_name).contains(keyword.lower()),
                    )
                    .all()
                )

                for feedback in feedbacks:
                    # Calculate match score based on how many keywords match
                    expense = (
                        session.query(Expense)
                        .filter(Expense.id == feedback.expense_id)
                        .first()
                    )
                    if expense:
                        expense_keywords = self.extract_keywords_from_text(
                            f"{expense.description or ''} {expense.merchant_name or ''}"
                        )
                        common_keywords = set(keywords) & set(expense_keywords)
                        score = len(common_keywords) / max(len(keywords), 1)

                        if score > best_score:
                            best_score = score
                            best_match = feedback

            if best_match and best_score >= 0.5:
                # Get the category
                category = (
                    session.query(Category)
                    .filter(Category.id == best_match.confirmed_category_id)
                    .first()
                )

                if category:
                    return {
                        "suggested_category_id": category.id,
                        "suggested_category_name": category.name,
                        "confidence_score": min(best_score * 0.9, 0.95),
                        "reason": "Based on similar past corrections",
                        "source": "feedback_history",
                    }

            return None

        except Exception as e:
            logger.error(f"Error getting suggestion from history: {str(e)}")
            return None

    def get_learning_statistics(
        self, user_id: str, db_session: Session = None
    ) -> Dict[str, Any]:
        """
        Get learning statistics for a user

        Args:
            user_id: User ID
            db_session: Database session

        Returns:
            Dictionary with learning statistics
        """
        try:
            session = db_session or self.db_session
            if not session:
                return {"error": "Database session required"}

            # Count rules
            total_rules = (
                session.query(ExpenseCategorizationRule)
                .filter(ExpenseCategorizationRule.user_id == user_id)
                .count()
            )

            active_rules = (
                session.query(ExpenseCategorizationRule)
                .filter(
                    ExpenseCategorizationRule.user_id == user_id,
                    ExpenseCategorizationRule.is_active == True,
                )
                .count()
            )

            # Count feedback
            total_feedback = (
                session.query(CategorizationFeedback)
                .filter(CategorizationFeedback.user_id == user_id)
                .count()
            )

            corrections = (
                session.query(CategorizationFeedback)
                .filter(
                    CategorizationFeedback.user_id == user_id,
                    CategorizationFeedback.feedback_type == "correction",
                )
                .count()
            )

            confirmations = (
                session.query(CategorizationFeedback)
                .filter(
                    CategorizationFeedback.user_id == user_id,
                    CategorizationFeedback.feedback_type == "confirmation",
                )
                .count()
            )

            # Calculate learning effectiveness
            learning_rate = (
                corrections / total_feedback * 100 if total_feedback > 0 else 0
            )

            return {
                "total_rules": total_rules,
                "active_rules": active_rules,
                "total_feedback": total_feedback,
                "corrections": corrections,
                "confirmations": confirmations,
                "learning_rate": round(learning_rate, 2),
                "message": f"Agent has learned {active_rules} rules from {corrections} corrections",
            }

        except Exception as e:
            logger.error(f"Error getting learning statistics: {str(e)}")
            return {"error": str(e)}
