"""
AI Interaction model for logging AI interactions
"""

from datetime import datetime
from typing import Optional
from uuid import uuid4
from sqlalchemy import Column, String, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from src.core.database import Base


class AIInteraction(Base):
    __tablename__ = "ai_interactions"

    id = Column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    user_id = Column(
        UUID(as_uuid=False), ForeignKey("users.id"), nullable=True
    )  # Optional, unauthenticated users
    session_id = Column(String, nullable=True)  # To group related interactions
    interaction_type = Column(
        String, nullable=False
    )  # e.g., "invoice_processing", "categorization", "advice"
    input_data = Column(Text, nullable=False)  # What was sent to the AI
    output_data = Column(Text, nullable=False)  # What was received from the AI
    model_used = Column(String, nullable=False)  # e.g., "gemini-2.5-flash"
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="ai_interactions")

    def __repr__(self):
        return f"<AIInteraction(id={self.id}, type={self.interaction_type}, model={self.model_used})>"

    def to_dict(self):
        """Convert the AI interaction to a dictionary representation"""
        return {
            "id": str(self.id) if self.id else None,
            "user_id": str(self.user_id) if self.user_id else None,
            "session_id": self.session_id,
            "interaction_type": self.interaction_type,
            "input_data": self.input_data,
            "output_data": self.output_data,
            "model_used": self.model_used,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
