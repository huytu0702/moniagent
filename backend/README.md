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

Example values can be found in `.env.example`.

## Running with Docker

To run the application using Docker, follow these steps:

1. Make sure you have Docker and Docker Compose installed on your system.

2. You'll need to configure your Supabase cloud project:
   - Create a Supabase account at https://supabase.com/
   - Create a new project
   - Get your Project URL and Public anon key from the Project Settings > API

3. Create a `.env` file in the backend directory with your environment variables:
   ```bash
   cp .env.example .env
   # Edit .env to add your Supabase project details and other configuration values
   ```

4. Build and run the services:
   ```bash
   docker-compose up --build
   ```

5. Access the application at `http://localhost:8000`

6. To run in detached mode:
   ```bash
   docker-compose up --build -d
   ```

7. To stop the services:
   ```bash
   docker-compose down
   ```

## Running Tests

```bash
pytest
```