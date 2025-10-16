"""
Invoice service
"""

import logging
from datetime import datetime
from typing import Dict, Any, IO
from uuid import uuid4
from sqlalchemy.orm import Session
from src.models.invoice import Invoice
from src.models.expense import Expense
from src.services.ocr_service import OCRService
from src.core.config import settings
from src.utils.image_utils import validate_and_save_image


logger = logging.getLogger(__name__)


class InvoiceServiceError(Exception):
    """Custom exception for invoice service errors"""
    pass


class InvoiceService:
    """
    Service for handling invoice processing operations
    """
    
    def __init__(self):
        self.ocr_service = OCRService()
    
    def process_invoice_upload(self, file_data: IO[bytes], filename: str, user_id: str = None) -> Dict[str, Any]:
        """
        Process an uploaded invoice file through OCR and store the results
        
        Args:
            file_data: File-like object containing the uploaded file
            filename: Original name of the uploaded file
            user_id: ID of the user who uploaded the invoice (optional)
            
        Returns:
            Dictionary containing the processed invoice information
        """
        try:
            logger.info(f"Starting invoice processing for file: {filename}, user_id: {user_id}")
            
            # Validate and save the uploaded file
            saved_file_path = validate_and_save_image(file_data, filename)
            
            # Reset file pointer after saving
            file_data.seek(0)
            
            logger.debug(f"File saved to: {saved_file_path}")
            
            # Process the invoice through OCR
            logger.debug("Starting OCR processing...")
            ocr_result = self.ocr_service.process_invoice(file_data)
            logger.debug(f"OCR processing completed with result: {ocr_result}")
            
            # Validate OCR results
            self._validate_ocr_result(ocr_result)
            logger.debug("OCR result validation passed")
            
            # Create an invoice object to store the results
            invoice = Invoice(
                user_id=user_id,
                filename=filename,
                file_path=saved_file_path,
                store_name=ocr_result.get('store_name'),
                date=datetime.fromisoformat(ocr_result['date']) if ocr_result.get('date') else None,
                total_amount=ocr_result.get('total_amount'),
                status='processed'
            )
            
            # Create an associated expense if total_amount exists
            expense = None
            if ocr_result.get('total_amount'):
                expense = Expense(
                    user_id=user_id,
                    invoice_id=invoice.id,
                    description=f"Expense from {ocr_result.get('store_name', 'Unknown Store')}",
                    amount=ocr_result.get('total_amount'),
                    date=datetime.fromisoformat(ocr_result['date']) if ocr_result.get('date') else datetime.utcnow()
                )
            
            # Return the processed result
            result = {
                'invoice_id': invoice.id,
                'store_name': ocr_result.get('store_name'),
                'date': ocr_result.get('date'),
                'total_amount': ocr_result.get('total_amount'),
                'status': 'processed'
            }
            
            logger.info(f"Invoice processed successfully: {result}")
            return result
            
        except ValueError as e:
            logger.error(f"Validation error processing invoice: {str(e)}")
            raise InvoiceServiceError(f"Validation error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error processing invoice: {str(e)}")
            raise InvoiceServiceError(f"Error processing invoice: {str(e)}")
    
    def _validate_ocr_result(self, ocr_result: Dict[str, Any]) -> None:
        """
        Validate the OCR result to ensure it has required information
        
        Args:
            ocr_result: Dictionary containing OCR extraction results
            
        Raises:
            ValueError: If the OCR result is invalid
        """
        if not ocr_result:
            raise ValueError("OCR result is empty")
        
        # For MVP, we require at least one of the fields to be present
        required_fields = ['store_name', 'date', 'total_amount']
        has_any_field = any(ocr_result.get(field) is not None for field in required_fields)
        
        if not has_any_field:
            raise ValueError("OCR could not extract any of the required fields: store_name, date, total_amount")
        
        # Validate date format if present
        if ocr_result.get('date'):
            try:
                datetime.fromisoformat(ocr_result['date'])
            except ValueError:
                raise ValueError(f"Invalid date format: {ocr_result['date']}. Expected ISO format (YYYY-MM-DD)")
        
        # Validate total amount if present
        if ocr_result.get('total_amount') is not None:
            try:
                amount = float(ocr_result['total_amount'])
                if amount < 0:
                    raise ValueError("Total amount cannot be negative")
            except (TypeError, ValueError):
                raise ValueError(f"Invalid total amount: {ocr_result['total_amount']}. Must be a positive number")
    
    def get_user_invoices(self, user_id: str, db_session: Session) -> list:
        """
        Retrieve all invoices for a specific user
        
        Args:
            user_id: ID of the user whose invoices to retrieve
            db_session: Database session to use for the query
            
        Returns:
            List of invoice dictionaries
        """
        try:
            if not user_id:
                raise ValueError("User ID is required")
            
            invoices = db_session.query(Invoice).filter(Invoice.user_id == user_id).all()
            return [invoice.to_dict() for invoice in invoices]
        except Exception as e:
            logger.error(f"Error retrieving user invoices: {str(e)}")
            raise InvoiceServiceError(f"Error retrieving invoices: {str(e)}")
    
    def get_invoice_by_id(self, invoice_id: str, db_session: Session) -> Dict[str, Any]:
        """
        Retrieve a specific invoice by ID
        
        Args:
            invoice_id: ID of the invoice to retrieve
            db_session: Database session to use for the query
            
        Returns:
            Invoice dictionary
        """
        try:
            if not invoice_id:
                raise ValueError("Invoice ID is required")
                
            invoice = db_session.query(Invoice).filter(Invoice.id == invoice_id).first()
            if not invoice:
                raise ValueError(f"Invoice with id {invoice_id} not found")
            return invoice.to_dict()
        except ValueError:
            raise  # Re-raise value errors as they are validation errors
        except Exception as e:
            logger.error(f"Error retrieving invoice {invoice_id}: {str(e)}")
            raise InvoiceServiceError(f"Error retrieving invoice: {str(e)}")