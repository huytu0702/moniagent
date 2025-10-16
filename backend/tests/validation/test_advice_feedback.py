"""
Phase 6: Simulate user feedback for financial advice helpfulness.
"""

from src.services.financial_advice_service import FinancialAdviceService


def test_financial_advice_contains_recommendations():
    service = FinancialAdviceService()
    result = service.get_financial_advice(user_id="user-adv", period="monthly", db_session=None)
    assert result.get("advice")
    recs = result.get("recommendations", [])
    assert isinstance(recs, list)
    assert len(recs) > 0
