from __future__ import annotations

from fastapi import APIRouter

from .invoice_router import router as invoice_router
from .category_router import router as category_router


router = APIRouter(prefix="/api/v1")

# Include invoice endpoints
router.include_router(invoice_router, prefix="", tags=["invoices"])

# Include category endpoints
router.include_router(category_router, prefix="", tags=["categories"])


__all__ = ["router"]
