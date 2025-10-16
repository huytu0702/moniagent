"""
Category model
"""

from datetime import datetime
from typing import Optional
from uuid import uuid4
from sqlalchemy import Column, String, DateTime, Boolean, Integer, ForeignKey, Text
from sqlalchemy.orm import relationship
from src.core.database import Base


class Category(Base):
    __tablename__ = "categories"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    icon = Column(String, nullable=True)  # Unicode icon or emoji
    color = Column(String, nullable=True)  # Hex color code
    is_system_category = Column(
        Boolean, default=False
    )  # System-defined vs user-defined
    display_order = Column(Integer, default=0)  # Order for display in UI
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="categories")
    categorization_rules = relationship(
        "ExpenseCategorizationRule",
        back_populates="category",
        cascade="all, delete-orphan",
    )
    categorization_feedbacks = relationship(
        "CategorizationFeedback",
        back_populates="confirmed_category",
        foreign_keys="[CategorizationFeedback.confirmed_category_id]",
    )
    budgets = relationship(
        "Budget", back_populates="category", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Category(id={self.id}, name={self.name}, user_id={self.user_id})>"

    def to_dict(self):
        """Convert the category to a dictionary representation"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "description": self.description,
            "icon": self.icon,
            "color": self.color,
            "is_system_category": self.is_system_category,
            "display_order": self.display_order,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
