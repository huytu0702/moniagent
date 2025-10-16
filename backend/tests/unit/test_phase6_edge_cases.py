"""
Phase 6 unit tests for edge cases and polish items.
"""

import io
from datetime import datetime, timedelta

import pytest

from sqlalchemy.orm import Session

from src.services.ai_agent_service import AIAgentService
from src.services.expense_processing_service import ExpenseProcessingService


def test_future_date_is_rejected_in_validation(test_db_session: Session):
    service = ExpenseProcessingService(test_db_session)
    future_date = (datetime.utcnow() + timedelta(days=2)).date().isoformat()
    expense = {"merchant_name": "Test", "amount": 10.0, "date": future_date}

    is_valid = service.validate_extracted_expense(expense)
    assert is_valid is False


def test_ai_agent_no_extraction_guidance_message(test_db_session: Session):
    ai = AIAgentService(test_db_session)
    session = ai.start_session(user_id="user-x", session_title="Phase6")

    response_text, extracted, _, _ = ai.process_message(
        session.id, "hello there", message_type="text"
    )

    assert extracted is None
    assert "Please include: amount" in response_text


def test_ai_agent_image_unreadable_message(test_db_session: Session):
    ai = AIAgentService(test_db_session)
    session = ai.start_session(user_id="user-y")

    # Provide a non-existent path to simulate unreadable image
    response_text, extracted, _, _ = ai.process_message(
        session.id, "C:/path/does/not/exist.png", message_type="image"
    )

    assert extracted is None
    assert "couldn't read the image" in response_text.lower()


def test_invoice_unreadable_image_returns_400(api_client, auth_headers):
    # Upload invalid image bytes
    data = {"file": ("bad.txt", io.BytesIO(b"not-an-image"), "text/plain")}
    resp = api_client.post("/api/v1/invoices/process", files=data, headers=auth_headers)

    # Unsupported type should be 400
    assert resp.status_code == 400
