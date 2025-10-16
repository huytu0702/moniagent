"""
Invoice model
"""

from datetime import datetime
from typing import Optional
from uuid import uuid4
from sqlalchemy import Column, String, DateTime, Float, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from src.core.database import Base


class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)
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
    expenses = relationship(
        "Expense", back_populates="invoice", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Invoice(id={self.id}, store_name={self.store_name}, total_amount={self.total_amount})>"

    def to_dict(self):
        """Convert the invoice to a dictionary representation"""
        return {
            "id": str(self.id) if self.id else None,
            "user_id": str(self.user_id) if self.user_id else None,
            "filename": self.filename,
            "store_name": self.store_name,
            "date": self.date.isoformat() if self.date else None,
            "total_amount": self.total_amount,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
