from __future__ import annotations

from fastapi import APIRouter

from .invoice_router import router as invoice_router
from .category_router import router as category_router
from .budget_router import router as budget_router, spending_router
from .ai_agent_router import router as ai_agent_router
from .chat_router import router as chat_router
from .expense_router import router as expense_router
from .auth_router import router as auth_router


router = APIRouter(prefix="/v1")

# Include auth endpoints
router.include_router(auth_router, prefix="", tags=["auth"])

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

# Include chat endpoints
router.include_router(chat_router, prefix="", tags=["chat"])

# Include expense endpoints (User Story 2 - corrections)
router.include_router(expense_router, prefix="", tags=["expenses"])


__all__ = ["router"]
