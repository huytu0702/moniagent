"""
Invoice model
"""

from datetime import datetime
from typing import Optional
from uuid import uuid4
from sqlalchemy import Column, String, DateTime, Float, Text, ForeignKey
from sqlalchemy.orm import relationship
from src.core.database import Base


class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    filename = Column(String, nullable=False)
    file_path = Column(Text, nullable=False)  # Path to stored file
    store_name = Column(String, nullable=True)
    date = Column(DateTime, nullable=True)  # Date of purchase
    total_amount = Column(Float, nullable=True)
    extracted_data = Column(Text, nullable=True)  # Raw extracted data as JSON
    status = Column(String, default="pending")  # pending, processed, failed
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    user = relationship("User", back_populates="invoices")
    expenses = relationship("Expense", back_populates="invoice", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Invoice(id={self.id}, store_name={self.store_name}, total_amount={self.total_amount})>"

    def to_dict(self):
        """Convert the invoice to a dictionary representation"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "filename": self.filename,
            "store_name": self.store_name,
            "date": self.date.isoformat() if self.date else None,
            "total_amount": self.total_amount,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }