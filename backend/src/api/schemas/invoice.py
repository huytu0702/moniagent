from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class InvoiceResponse(BaseModel):
    """Response model for invoice processing"""
    invoice_id: str
    store_name: Optional[str] = None
    date: Optional[str] = None
    total_amount: Optional[float] = None
    status: str


class InvoiceListResponse(BaseModel):
    """Response model for list of invoices"""
    invoices: List[InvoiceResponse]


class ProcessInvoiceRequest(BaseModel):
    """Request model for invoice processing"""
    filename: str
    file_content: bytes  # This will be handled differently in the actual API via UploadFile


__all__ = ["InvoiceResponse", "InvoiceListResponse", "ProcessInvoiceRequest"]