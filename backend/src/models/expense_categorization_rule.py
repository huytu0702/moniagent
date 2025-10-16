"""
ExpenseCategorizationRule model
"""

from datetime import datetime
from typing import Optional
from uuid import uuid4
from sqlalchemy import Column, String, DateTime, Boolean, Float, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from src.core.database import Base


class ExpenseCategorizationRule(Base):
    __tablename__ = "expense_categorization_rules"

    id = Column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)
    category_id = Column(
        UUID(as_uuid=False), ForeignKey("categories.id"), nullable=False
    )
    store_name_pattern = Column(String, nullable=False)  # Pattern to match store names
    rule_type = Column(String, default="keyword")  # keyword, regex, exact_match
    confidence_threshold = Column(
        Float, default=0.8
    )  # Minimum confidence for auto-categorization
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="categorization_rules")
    category = relationship("Category", back_populates="categorization_rules")

    def __repr__(self):
        return f"<ExpenseCategorizationRule(id={self.id}, category_id={self.category_id}, pattern={self.store_name_pattern})>"

    def to_dict(self):
        """Convert the rule to a dictionary representation"""
        return {
            "id": str(self.id) if self.id else None,
            "user_id": str(self.user_id) if self.user_id else None,
            "category_id": str(self.category_id) if self.category_id else None,
            "store_name_pattern": self.store_name_pattern,
            "rule_type": self.rule_type,
            "confidence_threshold": self.confidence_threshold,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
