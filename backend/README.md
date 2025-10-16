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

### Environment Variables

Create a file `.env` in `backend/` (or export in your shell) with:

```
APP_NAME=Financial Assistant API
ENV=development
LOG_LEVEL=INFO

# Supabase
SUPABASE_URL=<your_supabase_url>
SUPABASE_ANON_KEY=<your_supabase_anon_key>
# Optional for server-side admin
SUPABASE_SERVICE_ROLE_KEY=

# Security
JWT_SECRET=<a-long-random-string>
ACCESS_TOKEN_EXPIRE_MINUTES=60

# AI
GOOGLE_API_KEY=<your_google_api_key>
```

Example values can be found in `env.example`.

## Running Tests

```bash
pytest
```