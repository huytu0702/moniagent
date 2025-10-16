"""
AI Agent API router for financial advice and insights
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from src.core.security import get_current_user
from src.services.financial_advice_service import FinancialAdviceService
from src.api.schemas.budget import FinancialAdviceResponse


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/financial-advice", tags=["ai-agent"])
advice_service = FinancialAdviceService()


@router.get("", response_model=FinancialAdviceResponse)
async def get_financial_advice(
    period: str = Query(
        default="monthly", description="Period: daily, weekly, monthly"
    ),
    current_user: dict = Depends(get_current_user),
):
    """
    Get AI-driven financial advice for the current user

    Args:
        period: Time period to analyze (daily, weekly, monthly)
        current_user: Current authenticated user

    Returns:
        Financial advice with recommendations and spending pattern analysis
    """
    try:
        user_id = current_user.id if hasattr(current_user, 'id') else current_user['id']
        logger.info(f"Generating financial advice for user {user_id}, period {period}")

        advice = advice_service.get_financial_advice(user_id=user_id, period=period)

        return FinancialAdviceResponse(**advice)

    except Exception as e:
        logger.error(f"Error generating financial advice: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
