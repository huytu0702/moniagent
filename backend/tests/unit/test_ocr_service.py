"""
Unit test for OCR service
"""

import pytest
from unittest.mock import patch, MagicMock
from PIL import Image
import io
from src.services.ocr_service import OCRService


@pytest.fixture
def ocr_service():
    """Create an instance of OCRService"""
    return OCRService()


@pytest.fixture
def sample_invoice_image():
    """Create a sample invoice image for testing"""
    img = Image.new('RGB', (400, 300), color='white')
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='JPEG')
    img_byte_arr.seek(0)
    return img_byte_arr


def test_process_invoice_success(ocr_service, sample_invoice_image):
    """Test successful processing of an invoice image"""

    # Mock the Gemini API response
    with patch('src.services.ocr_service.genai') as mock_genai:
        mock_model = MagicMock()
        mock_genai.GenerativeModel.return_value = mock_model

        mock_response = MagicMock()
        mock_response.text = '{"store_name": "Grocery Store", "date": "2023-10-15", "total_amount": 42.50}'
        mock_model.generate_content.return_value = mock_response

        result = ocr_service.process_invoice(sample_invoice_image)

        # Verify the result structure
        assert "store_name" in result
        assert "date" in result
        assert "total_amount" in result

        # Verify the values
        assert result["store_name"] == "Grocery Store"
        assert result["date"] == "2023-10-15"
        assert result["total_amount"] == 42.50

        # Verify that the model was called
        mock_model.generate_content.assert_called_once()
        # The call should have been made with a list containing prompt and image
        args, kwargs = mock_model.generate_content.call_args
        assert len(args[0]) == 2  # prompt and image


def test_process_invoice_with_different_image_formats(ocr_service):
    """Test processing with different image formats"""

    # Test with PNG
    png_img = Image.new('RGBA', (400, 300), color='white')
    png_byte_arr = io.BytesIO()
    png_img.save(png_byte_arr, format='PNG')
    png_byte_arr.seek(0)

    with patch('src.services.ocr_service.genai') as mock_genai:
        mock_model = MagicMock()
        mock_genai.GenerativeModel.return_value = mock_model

        mock_response = MagicMock()
        mock_response.text = '{"store_name": "Electronics Store", "date": "2023-10-16", "total_amount": 199.99}'
        mock_model.generate_content.return_value = mock_response

        result = ocr_service.process_invoice(png_byte_arr)

        assert result["store_name"] == "Electronics Store"


def test_process_invoice_with_invalid_image(ocr_service):
    """Test handling of invalid image data"""

    # Create invalid image data
    invalid_data = io.BytesIO(b"this is not an image")

    with patch('src.services.ocr_service.Image') as mock_image:
        # Simulate an error when trying to open the image
        mock_image.open.side_effect = Exception("cannot identify image file")

        with pytest.raises(Exception) as exc_info:
            ocr_service.process_invoice(invalid_data)

        assert "cannot identify image file" in str(exc_info.value)


def test_gemini_api_call_format(ocr_service, sample_invoice_image):
    """Test that the Gemini API is called with the correct format"""

    with patch('src.services.ocr_service.genai') as mock_genai:
        mock_model = MagicMock()
        mock_genai.GenerativeModel.return_value = mock_model

        mock_response = MagicMock()
        mock_response.text = (
            '{"store_name": "Test Store", "date": "2023-10-17", "total_amount": 32.99}'
        )
        mock_model.generate_content.return_value = mock_response

        ocr_service.process_invoice(sample_invoice_image)

        # Verify the call was made correctly
        mock_model.generate_content.assert_called_once()
        args, kwargs = mock_model.generate_content.call_args

        # The call should be with a list [prompt_text, image]
        assert isinstance(args[0], list)
        assert len(args[0]) == 2

        # First element should contain the prompt text
        prompt_and_image = args[0]
        # Check that prompt is a string with expected keywords
        prompt_text = str(prompt_and_image[0]).lower()
        assert "extract" in prompt_text
        assert "store" in prompt_text or "merchant" in prompt_text
        assert "date" in prompt_text
        assert "total" in prompt_text and "amount" in prompt_text


def test_process_invoice_empty_response(ocr_service, sample_invoice_image):
    """Test handling of empty responses from the API"""

    with patch('src.services.ocr_service.genai') as mock_genai:
        mock_model = MagicMock()
        mock_genai.GenerativeModel.return_value = mock_model

        mock_response = MagicMock()
        mock_response.text = ''
        mock_model.generate_content.return_value = mock_response

        with pytest.raises(ValueError) as exc_info:
            ocr_service.process_invoice(sample_invoice_image)

        assert "Invalid JSON response from OCR" in str(exc_info.value)


def test_process_invoice_invalid_json_response(ocr_service, sample_invoice_image):
    """Test handling of invalid JSON responses from the API"""

    with patch('src.services.ocr_service.genai') as mock_genai:
        mock_model = MagicMock()
        mock_genai.GenerativeModel.return_value = mock_model

        mock_response = MagicMock()
        mock_response.text = 'not a valid json'
        mock_model.generate_content.return_value = mock_response

        with pytest.raises(ValueError) as exc_info:
            ocr_service.process_invoice(sample_invoice_image)

        assert "Invalid JSON response from OCR" in str(exc_info.value)


def test_process_invoice_missing_fields(ocr_service, sample_invoice_image):
    """Test handling of JSON responses with missing required fields"""

    with patch('src.services.ocr_service.genai') as mock_genai:
        mock_model = MagicMock()
        mock_genai.GenerativeModel.return_value = mock_model

        mock_response = MagicMock()
        # Missing required fields
        mock_response.text = '{"store_name": "Test Store", "date": "2023-10-17"}'
        mock_model.generate_content.return_value = mock_response

        result = ocr_service.process_invoice(sample_invoice_image)

        # Should still have store_name and date
        assert result["store_name"] == "Test Store"
        assert result["date"] == "2023-10-17"
        # total_amount should have a default value
        assert "total_amount" in result
        assert result["total_amount"] == 0.0
