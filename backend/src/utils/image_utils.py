"""
Image utility functions for handling file uploads
"""

import os
import uuid
from typing import IO
from pathlib import Path
from PIL import Image
from src.core.config import settings


def validate_and_save_image(file_data: IO[bytes], original_filename: str) -> str:
    """
    Validate and save an uploaded image file to the designated storage location.
    
    Args:
        file_data: File-like object containing the uploaded file
        original_filename: Original name of the uploaded file
        
    Returns:
        The path where the file was saved
    """
    # Allowed file extensions
    allowed_extensions = {'.jpg', '.jpeg', '.png'}
    
    # Extract file extension and validate
    file_extension = Path(original_filename).suffix.lower()
    
    if file_extension not in allowed_extensions:
        raise ValueError(f"File type not supported: {file_extension}. Allowed types: {allowed_extensions}")
    
    # Validate the image by attempting to open it
    try:
        img = Image.open(file_data)
        img.verify()  # Verify that it's a valid image
        file_data.seek(0)  # Reset file pointer after verification
    except Exception:
        raise ValueError("Uploaded file is not a valid image")
    
    # Create a unique filename to avoid conflicts
    unique_filename = f"{str(uuid.uuid4())}{file_extension}"
    
    # Determine the upload directory
    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(exist_ok=True)
    
    # Construct the full file path
    file_path = upload_dir / unique_filename
    
    # Save the file
    with open(file_path, 'wb') as f:
        f.write(file_data.read())
    
    return str(file_path)


def validate_image_content_type(content_type: str) -> bool:
    """
    Validate the content type of an uploaded file.
    
    Args:
        content_type: The content type of the uploaded file
        
    Returns:
        True if the content type is valid, False otherwise
    """
    valid_content_types = [
        'image/jpeg',
        'image/jpg', 
        'image/png'
    ]
    
    return content_type.lower() in valid_content_types


def validate_file_size(file_data: IO[bytes], max_size_mb: int = 10) -> bool:
    """
    Validate the size of an uploaded file.
    
    Args:
        file_data: File-like object containing the uploaded file
        max_size_mb: Maximum allowed file size in megabytes
        
    Returns:
        True if the file size is valid, False otherwise
    """
    # Store the current position
    current_pos = file_data.tell()
    
    # Move to the end of the file to get its size
    file_data.seek(0, os.SEEK_END)
    file_size = file_data.tell()
    
    # Move back to the original position
    file_data.seek(current_pos)
    
    max_size_bytes = max_size_mb * 1024 * 1024
    
    return file_size <= max_size_bytes