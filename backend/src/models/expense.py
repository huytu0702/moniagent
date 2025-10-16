"""
Expense model
"""

from datetime import datetime
from typing import Optional
from uuid import uuid4
from sqlalchemy import Column, String, DateTime, Float, Text, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from src.core.database import Base


class Expense(Base):
    __tablename__ = "expenses"

    id = Column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)
    invoice_id = Column(
        UUID(as_uuid=False), ForeignKey("invoices.id"), nullable=True
    )  # Can be null if not from invoice
    category_id = Column(
        UUID(as_uuid=False), ForeignKey("expense_categories.id"), nullable=True
    )
    description = Column(Text, nullable=True)
    merchant_name = Column(String, nullable=True)  # Name of location/restaurant
    amount = Column(Float, nullable=False)
    date = Column(DateTime, nullable=True)  # Date of expense
    confirmed_by_user = Column(
        Boolean, default=False
    )  # Whether user confirmed extracted info
    source_type = Column(String, nullable=True)  # "image" or "text"
    source_metadata = Column(Text, nullable=True)  # JSON metadata about source
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="expenses")
    invoice = relationship("Invoice", back_populates="expenses")
    category = relationship("ExpenseCategory", back_populates="expenses")
    categorization_feedbacks = relationship(
        "CategorizationFeedback", back_populates="expense", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Expense(id={self.id}, amount={self.amount}, merchant_name={self.merchant_name})>"

    def to_dict(self):
        """Convert the expense to a dictionary representation"""
        return {
            "id": str(self.id) if self.id else None,
            "user_id": str(self.user_id) if self.user_id else None,
            "invoice_id": str(self.invoice_id) if self.invoice_id else None,
            "category_id": str(self.category_id) if self.category_id else None,
            "description": self.description,
            "merchant_name": self.merchant_name,
            "amount": self.amount,
            "date": self.date.isoformat() if self.date else None,
            "confirmed_by_user": self.confirmed_by_user,
            "source_type": self.source_type,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
