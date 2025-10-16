"""
OCR service using Google's Gemini AI
"""

import json
import logging
from typing import Dict, Any, IO
from io import BytesIO
from PIL import Image
import google.generativeai as genai
from src.core.config import settings


logger = logging.getLogger(__name__)


class OCRService:
    """
    Service for processing invoices using Google's Gemini AI to extract
    store name, date, and total amount.
    """

    def __init__(self):
        # Initialize the Gemini API with the API key from settings
        # Only configure if API key is available (for testing purposes)
        self.api_key = settings.google_api_key
        if self.api_key:
            genai.configure(api_key=self.api_key)

        # Use the gemini-2.5-flash model for faster processing
        # This will be initialized on first use to support mocking in tests
        self._model = None

    @property
    def model(self):
        """Lazy initialization of the model to support mocking in tests."""
        if self._model is None:
            self._model = genai.GenerativeModel('gemini-2.5-flash')
        return self._model

    def process_invoice(self, image_data: IO[bytes]) -> Dict[str, Any]:
        """
        Process an invoice image and extract key information.

        Args:
            image_data: File-like object containing image data

        Returns:
            Dict containing extracted information (store_name, date, total_amount)
        """
        try:
            # Log the start of the operation
            logger.info("Starting invoice processing with OCR")

            # Load the image from the file-like object
            image = Image.open(image_data)

            # Prepare the prompt for the Gemini model
            prompt = """
            Analyze this invoice/receipt and extract the following information:
            1. Store/merchant name
            2. Date of purchase (in YYYY-MM-DD format)
            3. Total amount (as a decimal number)
            
            Respond ONLY with a valid JSON object in the following format:
            {
                "store_name": "string",
                "date": "YYYY-MM-DD",
                "total_amount": number
            }
            
            If any information is not available, use null for that field.
            Do not include any explanation or text outside the JSON object.
            """

            # Log the API call
            logger.debug("Sending request to Gemini AI API for invoice processing")

            # Generate content using the model
            response = self.model.generate_content([prompt, image])

            # Extract the text response
            response_text = response.text.strip()

            # Remove any markdown code block formatting if present
            if response_text.startswith('```json'):
                response_text = response_text[7:]  # Remove ```json
            if response_text.startswith('```'):
                response_text = response_text[3:]  # Remove ```
            if response_text.endswith('```'):
                response_text = response_text[:-3]  # Remove ```

            # Log the raw response for debugging (truncated to avoid very long logs)
            logger.debug(f"Gemini API response received, length: {len(response_text)}")

            # Parse the JSON response
            extracted_data = json.loads(response_text)

            # Ensure required fields exist, with defaults if needed
            result = {
                "store_name": extracted_data.get("store_name"),
                "date": extracted_data.get("date"),
                "total_amount": extracted_data.get("total_amount", 0.0),
            }

            logger.info(f"Successfully extracted invoice data: {result}")
            return result

        except json.JSONDecodeError as e:
            logger.error(
                f"Invalid JSON response from OCR: {response_text if 'response_text' in locals() else 'Response not available'}"
            )
            raise ValueError("Invalid JSON response from OCR")

        except Exception as e:
            logger.error(f"Error processing invoice with OCR: {str(e)}")
            raise e
