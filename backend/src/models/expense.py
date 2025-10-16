"""
Expense model
"""

from datetime import datetime
from typing import Optional
from uuid import uuid4
from sqlalchemy import Column, String, DateTime, Float, Text, ForeignKey
from sqlalchemy.orm import relationship
from src.core.database import Base


class Expense(Base):
    __tablename__ = "expenses"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    invoice_id = Column(
        String, ForeignKey("invoices.id"), nullable=True
    )  # Can be null if not from invoice
    description = Column(Text, nullable=True)
    amount = Column(Float, nullable=False)
    category = Column(String, nullable=True)  # Will be set by categorization service
    date = Column(DateTime, nullable=True)  # Date of expense
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="expenses")
    invoice = relationship("Invoice", back_populates="expenses")
    categorization_feedbacks = relationship(
        "CategorizationFeedback", back_populates="expense", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return (
            f"<Expense(id={self.id}, amount={self.amount}, category={self.category})>"
        )

    def to_dict(self):
        """Convert the expense to a dictionary representation"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "invoice_id": self.invoice_id,
            "description": self.description,
            "amount": self.amount,
            "category": self.category,
            "date": self.date.isoformat() if self.date else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
