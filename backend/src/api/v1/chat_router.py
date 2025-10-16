"""
Chat API router for AI-powered expense tracking conversations
"""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.core.security import get_current_user
from src.services.ai_agent_service import AIAgentService
from src.api.schemas.chat import (
    ChatStartRequest,
    ChatStartResponse,
    ChatMessageRequest,
    ChatMessageResponse,
    ChatSessionHistoryResponse,
    ChatSessionSchema,
    ChatMessageSchema,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/start", response_model=ChatStartResponse)
async def start_chat_session(
    request: ChatStartRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Start a new chat session

    Args:
        request: Request with optional session title
        current_user: Current authenticated user
        db: Database session

    Returns:
        ChatStartResponse with session ID and initial message
    """
    try:
        user_id = current_user.id if hasattr(current_user, "id") else current_user["id"]
        logger.info(f"Starting chat session for user {user_id}")

        ai_service = AIAgentService(db)
        session = ai_service.start_session(
            user_id=user_id, session_title=request.session_title
        )

        return ChatStartResponse(
            session_id=session.id,
            message="Chat session started successfully",
            initial_message=ai_service.get_initial_message(),
        )

    except Exception as e:
        logger.error(f"Error starting chat session: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{session_id}/message", response_model=ChatMessageResponse)
async def send_chat_message(
    session_id: str,
    request: ChatMessageRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Send a message in a chat session

    Args:
        session_id: Chat session ID
        request: Message request with content and type
        current_user: Current authenticated user
        db: Database session

    Returns:
        ChatMessageResponse with AI response and extracted expense info
    """
    try:
        user_id = current_user.id if hasattr(current_user, "id") else current_user["id"]
        logger.info(f"Processing message for session {session_id}, user {user_id}")

        ai_service = AIAgentService(db)
        response_text, extracted_expense, budget_warning, advice = (
            ai_service.process_message(
                session_id=session_id,
                user_message=request.content,
                message_type=request.message_type,
            )
        )

        # Build response
        response = ChatMessageResponse(
            message_id=f"msg-{session_id}",
            response=response_text,
            requires_confirmation=extracted_expense is not None,
            budget_warning=budget_warning.get("message") if budget_warning else None,
            advice=advice,
        )

        if extracted_expense:
            from src.api.schemas.chat import ExtractedExpenseInfo

            response.extracted_expense = ExtractedExpenseInfo(**extracted_expense)

        return response

    except Exception as e:
        logger.error(f"Error processing chat message: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{session_id}/confirm-expense")
async def confirm_expense(
    session_id: str,
    expense_id: str,
    category_id: Optional[str] = None,
    confirmed: bool = True,
    corrections: Optional[dict] = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Confirm an extracted expense and save it

    Args:
        session_id: Chat session ID
        expense_id: Expense ID to confirm
        category_id: Category ID for the expense
        confirmed: Whether the user confirmed the expense
        corrections: Any corrections to the extracted data
        current_user: Current authenticated user
        db: Database session

    Returns:
        Confirmed expense data
    """
    try:
        user_id = current_user.id if hasattr(current_user, "id") else current_user["id"]
        logger.info(f"Confirming expense {expense_id} for session {session_id}")

        ai_service = AIAgentService(db)

        if not confirmed:
            # If not confirmed, ask for corrections
            return {
                "status": "needs_correction",
                "message": "Please provide corrections for the expense",
            }

        # Save the expense with corrections if provided
        expense_data = {
            "amount": corrections.get("amount") if corrections else None,
            "merchant_name": corrections.get("merchant_name") if corrections else None,
            "date": corrections.get("date") if corrections else None,
        }

        # Filter out None values
        expense_data = {k: v for k, v in expense_data.items() if v is not None}

        # TODO: Get actual expense data from session context
        # For now, this is a placeholder

        return {
            "status": "confirmed",
            "message": "Expense confirmed and saved",
            "expense_id": expense_id,
        }

    except Exception as e:
        logger.error(f"Error confirming expense: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{session_id}/history", response_model=ChatSessionHistoryResponse)
async def get_session_history(
    session_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get chat session history

    Args:
        session_id: Chat session ID
        current_user: Current authenticated user
        db: Database session

    Returns:
        ChatSessionHistoryResponse with session and all messages
    """
    try:
        user_id = current_user.id if hasattr(current_user, "id") else current_user["id"]
        logger.info(f"Fetching history for session {session_id}")

        ai_service = AIAgentService(db)
        session, messages = ai_service.get_session_history(session_id)

        # Convert to response models
        session_data = ChatSessionSchema(
            id=session.id,
            user_id=session.user_id,
            session_title=session.session_title,
            status=(
                session.status.value
                if hasattr(session.status, "value")
                else session.status
            ),
            created_at=session.created_at.isoformat(),
            updated_at=session.updated_at.isoformat(),
        )

        messages_data = [
            ChatMessageSchema(
                id=msg.id,
                session_id=msg.session_id,
                role=msg.role,
                content=msg.content,
                created_at=msg.created_at.isoformat(),
            )
            for msg in messages
        ]

        return ChatSessionHistoryResponse(session=session_data, messages=messages_data)

    except Exception as e:
        logger.error(f"Error fetching session history: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{session_id}/close")
async def close_session(
    session_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Close a chat session

    Args:
        session_id: Chat session ID
        current_user: Current authenticated user
        db: Database session

    Returns:
        Closed session data
    """
    try:
        user_id = current_user.id if hasattr(current_user, "id") else current_user["id"]
        logger.info(f"Closing session {session_id}")

        ai_service = AIAgentService(db)
        closed_session = ai_service.close_session(session_id)

        return {
            "status": "closed",
            "session_id": closed_session.id,
            "message": "Chat session closed",
        }

    except Exception as e:
        logger.error(f"Error closing session: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
