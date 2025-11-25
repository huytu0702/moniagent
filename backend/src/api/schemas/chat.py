"""
Chat API schemas and DTOs
"""

from typing import List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field


class ChatMessageSchema(BaseModel):
    """Schema for a chat message"""

    id: str
    session_id: str
    role: str  # "user" or "assistant"
    content: str
    created_at: str

    class Config:
        json_schema_extra = {
            "example": {
                "id": "msg-123",
                "session_id": "session-456",
                "role": "user",
                "content": "I spent $25 on coffee",
                "created_at": "2025-10-16T10:00:00",
            }
        }


class ChatSessionSchema(BaseModel):
    """Schema for a chat session"""

    id: str
    user_id: str
    session_title: Optional[str]
    status: str
    created_at: str
    updated_at: str

    class Config:
        json_schema_extra = {
            "example": {
                "id": "session-123",
                "user_id": "user-456",
                "session_title": "Expense Tracking Session",
                "status": "active",
                "created_at": "2025-10-16T10:00:00",
                "updated_at": "2025-10-16T10:00:00",
            }
        }


class ChatStartRequest(BaseModel):
    """Request to start a new chat session"""

    session_title: Optional[str] = Field(
        None, description="Optional title for the chat session"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "session_title": "October Expense Tracking",
            }
        }


class ChatStartResponse(BaseModel):
    """Response when starting a chat session"""

    session_id: str
    message: str
    initial_message: str

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "session-123",
                "message": "Chat session started",
                "initial_message": "Hello! I'm your AI assistant for expense tracking. You can upload an invoice image or describe your expense. What would you like to do?",
            }
        }


class ChatMessageRequest(BaseModel):
    """Request to send a message in a chat session"""

    content: str = Field(..., description="Message content")
    message_type: str = Field(
        default="text", description="Type of message: text or image"
    )
    is_confirmation_response: bool = Field(
        default=False, description="Whether this is a response to confirmation prompt"
    )
    saved_expense: Optional[dict] = Field(
        None, description="Saved expense data (for client-side tracking when is_confirmation_response=True)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "content": "I spent $25 on coffee at Starbucks today",
                "message_type": "text",
                "is_confirmation_response": False,
                "saved_expense": None,
            }
        }


class ExtractedExpenseInfo(BaseModel):
    """Schema for extracted expense information"""

    merchant_name: Optional[str] = Field(None, description="Name of merchant/location")
    amount: float = Field(..., description="Expense amount", gt=0)
    date: Optional[str] = Field(None, description="Date of expense (YYYY-MM-DD)")
    confidence: float = Field(..., description="Confidence level of extraction (0-1)")
    description: Optional[str] = Field(None, description="Additional description")
    suggested_category_id: Optional[str] = Field(
        None, description="Auto-suggested category ID based on merchant and rules"
    )
    categorization_confidence: Optional[float] = Field(
        None, description="Confidence level of categorization suggestion (0-1)"
    )


class ChatMessageResponse(BaseModel):
    """Response with chat message and extracted info"""

    message_id: str
    response: str
    extracted_expense: Optional[ExtractedExpenseInfo] = None
    requires_confirmation: bool = Field(
        False, description="Whether expense requires user confirmation"
    )
    asking_confirmation: bool = Field(
        False, description="Whether agent is asking for confirmation/update"
    )
    saved_expense: Optional[dict] = Field(
        None, description="Details of saved expense (when asking_confirmation=True)"
    )
    budget_warning: Optional[str] = None
    advice: Optional[str] = None
    interrupted: bool = Field(
        False, description="Whether graph execution was interrupted (waiting for user response)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "message_id": "msg-789",
                "response": "I found an expense: $25.00 at Starbucks. Is this correct?",
                "extracted_expense": {
                    "merchant_name": "Starbucks",
                    "amount": 25.00,
                    "date": "2025-10-16",
                    "confidence": 0.95,
                    "suggested_category_id": "cat-food-dining",
                    "categorization_confidence": 0.9,
                },
                "requires_confirmation": True,
                "asking_confirmation": False,
                "saved_expense": None,
                "budget_warning": None,
                "advice": None,
                "interrupted": False,
            }
        }


class ExpenseConfirmationRequest(BaseModel):
    """Request to confirm extracted expense"""

    confirmed: bool = Field(..., description="Whether expense is confirmed")
    corrections: Optional[dict] = Field(
        None, description="Any corrections to the extracted info"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "confirmed": True,
                "corrections": None,
            }
        }


class ChatSessionHistoryResponse(BaseModel):
    """Response with full chat session history"""

    session: ChatSessionSchema
    messages: List[ChatMessageSchema]
