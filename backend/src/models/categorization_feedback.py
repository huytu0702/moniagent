"""
CategorizationFeedback model
"""

from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, DateTime, Float, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from src.core.database import Base


class CategorizationFeedback(Base):
    __tablename__ = "categorization_feedback"

    id = Column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)
    expense_id = Column(UUID(as_uuid=False), ForeignKey("expenses.id"), nullable=False)
    suggested_category_id = Column(
        UUID(as_uuid=False), ForeignKey("categories.id"), nullable=True
    )
    confirmed_category_id = Column(
        UUID(as_uuid=False), ForeignKey("categories.id"), nullable=False
    )
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
            "id": str(self.id) if self.id else None,
            "user_id": str(self.user_id) if self.user_id else None,
            "expense_id": str(self.expense_id) if self.expense_id else None,
            "suggested_category_id": (
                str(self.suggested_category_id) if self.suggested_category_id else None
            ),
            "confirmed_category_id": (
                str(self.confirmed_category_id) if self.confirmed_category_id else None
            ),
            "confidence_score": self.confidence_score,
            "feedback_type": self.feedback_type,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
