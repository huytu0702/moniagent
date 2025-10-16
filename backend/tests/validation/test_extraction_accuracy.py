"""
Phase 6 accuracy validation tests for text extraction.
"""

from sqlalchemy.orm import Session

from src.services.expense_processing_service import ExpenseProcessingService


def test_extract_amount_and_merchant_simple_sentence(test_db_session: Session):
    svc = ExpenseProcessingService(test_db_session)
    data = svc.extract_expense_from_text("I spent $19.99 at Starbucks yesterday")
    assert isinstance(data, dict)
    assert data.get("amount") == 19.99
    assert data.get("merchant_name") is not None


def test_extract_amount_from_varied_format(test_db_session: Session):
    svc = ExpenseProcessingService(test_db_session)
    samples = [
        "Lunch cost $12",
        "Paid 12.00 for lunch",
        "$12 lunch",
        "Total: $12.00",
    ]
    for s in samples:
        d = svc.extract_expense_from_text(s)
        assert d.get("amount") in (12.0, 12), f"Failed to parse amount from '{s}'"
