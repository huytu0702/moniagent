"""
Invoice API router
"""

from typing import List
from fastapi import APIRouter, File, UploadFile, Depends, HTTPException, status
from sqlalchemy.orm import Session
from src.api.schemas.invoice import InvoiceResponse, InvoiceListResponse
from src.services.invoice_service import InvoiceService
from src.core.database import get_db
from src.core.security import get_current_user
from src.models.user import User


router = APIRouter(prefix="/invoices", tags=["invoices"])


@router.post("/process", response_model=InvoiceResponse)
async def process_invoice(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload and process an invoice using OCR to extract store name, date, and total amount
    """
    # Check if file type is allowed
    allowed_types = ["image/jpeg", "image/jpg", "image/png"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not supported. Allowed types: {allowed_types}"
        )
    
    try:
        # Process the invoice using the service
        invoice_service = InvoiceService()
        result = invoice_service.process_invoice_upload(
            file.file, 
            file.filename, 
            current_user.id
        )
        
        return InvoiceResponse(
            invoice_id=result['invoice_id'],
            store_name=result['store_name'],
            date=result['date'],
            total_amount=result['total_amount'],
            status=result['status']
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing invoice: {str(e)}"
        )


@router.get("/", response_model=InvoiceListResponse)
async def get_user_invoices(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all invoices for the current user
    """
    try:
        invoice_service = InvoiceService()
        invoices = invoice_service.get_user_invoices(current_user.id, db)
        
        return InvoiceListResponse(invoices=invoices)
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving invoices: {str(e)}"
        )


@router.get("/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(
    invoice_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific invoice by ID
    """
    try:
        invoice_service = InvoiceService()
        invoice = invoice_service.get_invoice_by_id(invoice_id, db)
        
        # Check if the invoice belongs to the current user
        if invoice['user_id'] != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this invoice"
            )
        
        return InvoiceResponse(
            invoice_id=invoice['id'],
            store_name=invoice['store_name'],
            date=invoice['date'],
            total_amount=invoice['total_amount'],
            status=invoice['status']
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving invoice: {str(e)}"
        )