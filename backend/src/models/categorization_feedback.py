"""
CategorizationFeedback model
"""

from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, DateTime, Float, ForeignKey
from sqlalchemy.orm import relationship
from src.core.database import Base


class CategorizationFeedback(Base):
    __tablename__ = "categorization_feedback"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    expense_id = Column(String, ForeignKey("expenses.id"), nullable=False)
    suggested_category_id = Column(String, ForeignKey("categories.id"), nullable=True)
    confirmed_category_id = Column(String, ForeignKey("categories.id"), nullable=False)
    confidence_score = Column(Float, nullable=True)  # Confidence of the suggestion
    feedback_type = Column(String, default="confirmation")  # confirmation, correction
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="categorization_feedbacks")
    expense = relationship("Expense", back_populates="categorization_feedbacks")
    suggested_category = relationship(
        "Category", foreign_keys=[suggested_category_id], viewonly=True
    )
    confirmed_category = relationship(
        "Category",
        back_populates="categorization_feedbacks",
        foreign_keys=[confirmed_category_id],
    )

    def __repr__(self):
        return f"<CategorizationFeedback(id={self.id}, expense_id={self.expense_id}, type={self.feedback_type})>"

    def to_dict(self):
        """Convert the feedback to a dictionary representation"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "expense_id": self.expense_id,
            "suggested_category_id": self.suggested_category_id,
            "confirmed_category_id": self.confirmed_category_id,
            "confidence_score": self.confidence_score,
            "feedback_type": self.feedback_type,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
