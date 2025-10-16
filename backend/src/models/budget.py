"""
Budget model
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import uuid4
from sqlalchemy import Column, String, DateTime, Float, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from src.core.database import Base


class Budget(Base):
    __tablename__ = "budgets"

    id = Column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)
    category_id = Column(
        UUID(as_uuid=False), ForeignKey("expense_categories.id"), nullable=False
    )
    limit_amount = Column(Float, nullable=False)  # Monthly/weekly limit
    period = Column(String, default="monthly")  # 'monthly', 'weekly', 'yearly'
    alert_threshold = Column(
        Float, default=0.8
    )  # Alert when spending reaches this percentage (0.0-1.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="budgets")
    category = relationship("ExpenseCategory", back_populates="budgets")

    def __repr__(self):
        return f"<Budget(id={self.id}, user_id={self.user_id}, category_id={self.category_id}, limit_amount={self.limit_amount})>"

    def to_dict(self):
        """Convert the budget to a dictionary representation"""
        return {
            "id": str(self.id) if self.id else None,
            "user_id": str(self.user_id) if self.user_id else None,
            "category_id": str(self.category_id) if self.category_id else None,
            "limit_amount": self.limit_amount,
            "period": self.period,
            "alert_threshold": self.alert_threshold,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
