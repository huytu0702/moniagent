"""
Chat Session model for tracking conversation history with AI Agent
"""

from datetime import datetime
from typing import Optional
from uuid import uuid4
from enum import Enum
from sqlalchemy import Column, String, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from src.core.database import Base


class ChatSessionStatus(str, Enum):
    """Enum for chat session status values"""

    ACTIVE = "active"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    session_title = Column(String, nullable=True)
    status = Column(
        SQLEnum(ChatSessionStatus), default=ChatSessionStatus.ACTIVE, nullable=False
    )
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="chat_sessions")
    messages = relationship(
        "ChatMessage", back_populates="session", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return (
            f"<ChatSession(id={self.id}, user_id={self.user_id}, status={self.status})>"
        )

    def to_dict(self):
        """Convert the chat session to a dictionary representation"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "session_title": self.session_title,
            "status": (
                self.status.value
                if isinstance(self.status, ChatSessionStatus)
                else self.status
            ),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class ChatMessage(Base):
    """Represents individual messages in a chat session"""

    __tablename__ = "chat_messages"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    session_id = Column(String, ForeignKey("chat_sessions.id"), nullable=False)
    role = Column(String, nullable=False)  # "user" or "assistant"
    content = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    session = relationship("ChatSession", back_populates="messages")

    def __repr__(self):
        return f"<ChatMessage(id={self.id}, role={self.role}, session_id={self.session_id})>"

    def to_dict(self):
        """Convert the message to a dictionary representation"""
        return {
            "id": self.id,
            "session_id": self.session_id,
            "role": self.role,
            "content": self.content,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
