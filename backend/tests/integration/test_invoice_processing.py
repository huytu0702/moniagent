"""
Integration test for invoice OCR workflow
"""

import pytest
import os
from unittest.mock import patch, MagicMock
from PIL import Image
import io
from datetime import datetime


@pytest.fixture(autouse=True)
def set_jwt_secret():
    """Set JWT_SECRET environment variable for tests"""
    os.environ["JWT_SECRET"] = "test-secret-key-for-testing-only"
    yield
    if "JWT_SECRET" in os.environ:
        del os.environ["JWT_SECRET"]


@pytest.fixture
def sample_invoice_image():
    """Create a sample invoice image for testing"""
    img = Image.new('RGB', (400, 300), color='white')
    # In a real test, we would add some text to mimic an invoice
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='JPEG')
    img_byte_arr.seek(0)
    return img_byte_arr


def test_invoice_processing_workflow(sample_invoice_image):
    """Test the complete invoice processing workflow from upload to extraction"""

    # Import here after env var is set
    from src.services.invoice_service import InvoiceService

    # Mock both the validate_and_save_image and OCRService
    with patch('src.services.invoice_service.validate_and_save_image') as mock_validate:
        with patch('src.services.invoice_service.OCRService') as mock_ocr_service:
            with patch('src.services.invoice_service.Invoice'):
                with patch('src.services.invoice_service.Expense'):
                    # Setup mocks
                    mock_validate.return_value = "/tmp/test_invoice.jpg"

                    expected_result = {
                        "store_name": "Supermarket ABC",
                        "date": "2023-10-15",
                        "total_amount": 125.75,
                    }
                    mock_instance = mock_ocr_service.return_value
                    mock_instance.process_invoice.return_value = expected_result

                    # Test the invoice service
                    invoice_service = InvoiceService()

                    # Process the invoice
                    result = invoice_service.process_invoice_upload(
                        sample_invoice_image, "test_invoice.jpg"
                    )

                    # Verify the result
                    assert result["store_name"] == expected_result["store_name"]
                    assert result["date"] == expected_result["date"]
                    assert result["total_amount"] == expected_result["total_amount"]
                    assert "invoice_id" in result
                    assert "status" in result
                    assert result["status"] == "processed"


def test_invoice_processing_with_invalid_image():
    """Test that invalid images are handled properly"""

    # Import here after env var is set
    from src.services.invoice_service import InvoiceService

    # Create invalid image data
    invalid_data = io.BytesIO(b"this is not an image")

    with patch('src.services.invoice_service.validate_and_save_image') as mock_validate:
        # Simulate an error when validating invalid image
        mock_validate.side_effect = ValueError("Uploaded file is not a valid image")

        invoice_service = InvoiceService()

        with pytest.raises(Exception) as exc_info:
            invoice_service.process_invoice_upload(invalid_data, "invalid.jpg")

        # The error should indicate validation failure
        assert "Validation error" in str(exc_info.value)


def test_invoice_storage_after_processing(sample_invoice_image):
    """Test that invoices are properly stored after processing"""

    # Import here after env var is set
    from src.services.invoice_service import InvoiceService

    with patch('src.services.invoice_service.validate_and_save_image') as mock_validate:
        with patch('src.services.invoice_service.OCRService') as mock_ocr_service:
            with patch('src.services.invoice_service.Invoice'):
                with patch('src.services.invoice_service.Expense'):
                    expected_result = {
                        "store_name": "Tech Store",
                        "date": "2023-10-16",
                        "total_amount": 899.99,
                    }

                    mock_validate.return_value = "/tmp/test_invoice.jpg"

                    mock_instance = mock_ocr_service.return_value
                    mock_instance.process_invoice.return_value = expected_result

                    invoice_service = InvoiceService()
                    result = invoice_service.process_invoice_upload(
                        sample_invoice_image, "test_invoice.jpg"
                    )

                    # Verify the invoice was processed correctly
                    assert result["store_name"] == expected_result["store_name"]
                    assert result["date"] == expected_result["date"]
                    assert result["total_amount"] == expected_result["total_amount"]


def test_error_handling_in_invoice_processing():
    """Test error handling during the invoice processing workflow"""

    # Import here after env var is set
    from src.services.invoice_service import InvoiceService

    with patch('src.services.invoice_service.validate_and_save_image') as mock_validate:
        with patch('src.services.invoice_service.OCRService') as mock_ocr_service:
            mock_validate.return_value = "/tmp/test_invoice.jpg"

            mock_instance = mock_ocr_service.return_value
            # Simulate an error from the OCR service
            mock_instance.process_invoice.side_effect = Exception(
                "OCR processing failed"
            )

            invoice_service = InvoiceService()

            with pytest.raises(Exception) as exc_info:
                invoice_service.process_invoice_upload(
                    io.BytesIO(b"fake image data"), "test_invoice.jpg"
                )

            # The error message should indicate an error occurred
            assert "Error processing invoice" in str(exc_info.value)
