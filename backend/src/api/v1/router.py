from __future__ import annotations

from fastapi import APIRouter

from .invoice_router import router as invoice_router
from .category_router import router as category_router
from .budget_router import router as budget_router, spending_router
from .ai_agent_router import router as ai_agent_router


router = APIRouter(prefix="/api/v1")

# Include invoice endpoints
router.include_router(invoice_router, prefix="", tags=["invoices"])

# Include category endpoints
router.include_router(category_router, prefix="", tags=["categories"])

# Include budget endpoints
router.include_router(budget_router, prefix="", tags=["budgets"])

# Include spending summary endpoints
router.include_router(spending_router, prefix="", tags=["spending"])

# Include financial advice endpoints
router.include_router(ai_agent_router, prefix="", tags=["ai-agent"])


__all__ = ["router"]
