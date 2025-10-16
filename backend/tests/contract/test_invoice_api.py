"""
Contract test for invoice processing endpoint
"""

import pytest
import os
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from PIL import Image
import io
from src.api.main import app
from src.core.security import create_access_token


@pytest.fixture(autouse=True)
def set_jwt_secret():
    """Set JWT_SECRET environment variable for tests"""
    os.environ["JWT_SECRET"] = "test-secret-key-for-testing-only"
    yield
    # Cleanup after test
    if "JWT_SECRET" in os.environ:
        del os.environ["JWT_SECRET"]


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def auth_headers():
    """Create a valid JWT token for testing"""
    # Create a test token
    token = create_access_token(subject="test-user-id")
    return {"Authorization": f"Bearer {token}"}


def test_upload_invoice_endpoint_structure(client, auth_headers):
    """Test the structure of the invoice upload endpoint"""

    # Create a simple in-memory image for testing
    img = Image.new('RGB', (100, 100), color='red')
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='JPEG')
    img_byte_arr.seek(0)

    # Mock InvoiceService at the router level to prevent actual API calls
    with patch('src.api.v1.invoice_router.InvoiceService') as mock_service_class:
        mock_instance = mock_service_class.return_value
        mock_instance.process_invoice_upload.return_value = {
            "invoice_id": "test-id-123",
            "store_name": "Test Store",
            "date": "2023-10-15",
            "total_amount": 42.50,
            "status": "processed",
        }

        response = client.post(
            "/api/v1/invoices/process",
            files={"file": ("test_invoice.jpg", img_byte_arr, "image/jpeg")},
            headers=auth_headers,
        )

        assert response.status_code == 200

        # Verify response structure
        response_data = response.json()
        assert "invoice_id" in response_data
        assert "store_name" in response_data
        assert "date" in response_data
        assert "total_amount" in response_data
        assert "status" in response_data

        # Verify expected data types
        assert isinstance(response_data["invoice_id"], str)
        assert isinstance(response_data["store_name"], str)
        assert isinstance(response_data["date"], str)
        assert isinstance(response_data["total_amount"], (float, int))
        assert isinstance(response_data["status"], str)


def test_upload_invalid_file_type(client, auth_headers):
    """Test that invalid file types are rejected"""

    # Create a text file to simulate invalid upload
    txt_content = "This is not an image file"

    response = client.post(
        "/api/v1/invoices/process",
        files={"file": ("test.txt", txt_content, "text/plain")},
        headers=auth_headers,
    )

    assert response.status_code == 400
    response_data = response.json()
    assert "detail" in response_data


def test_missing_file(client, auth_headers):
    """Test that missing file uploads are handled properly"""

    response = client.post("/api/v1/invoices/process", headers=auth_headers)

    assert response.status_code == 422  # Unprocessable entity


def test_upload_invoice_different_formats(client, auth_headers):
    """Test upload with different image formats"""

    # Test with PNG
    img = Image.new('RGBA', (100, 100), color='blue')
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)

    with patch('src.api.v1.invoice_router.InvoiceService') as mock_service_class:
        mock_instance = mock_service_class.return_value
        mock_instance.process_invoice_upload.return_value = {
            "invoice_id": "test-id-456",
            "store_name": "Test Store",
            "date": "2023-10-15",
            "total_amount": 42.50,
            "status": "processed",
        }

        response = client.post(
            "/api/v1/invoices/process",
            files={"file": ("test_invoice.png", img_byte_arr, "image/png")},
            headers=auth_headers,
        )

        assert response.status_code == 200
        response_data = response.json()
        assert "store_name" in response_data
        assert response_data["store_name"] == "Test Store"
