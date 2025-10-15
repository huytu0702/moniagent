# Financial Assistant Backend

This is the backend service for the Financial Assistant with OCR and Expense Management application.

## Setup

1. Make sure you have Python 3.10+ installed
2. Create a virtual environment:
   ```bash
   python -m venv .venv
   ```
3. Activate the virtual environment:
   ```bash
   # On Windows
   .venv\Scripts\activate
   # On macOS/Linux
   source .venv/bin/activate
   ```
4. Install dependencies:
   ```bash
   pip install -e .
   # Or for development:
   pip install -e .[dev]
   ```

## Running the Application

```bash
uvicorn src.api.main:app --reload
```

## Running Tests

```bash
pytest
```