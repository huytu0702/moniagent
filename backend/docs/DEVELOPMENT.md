# Development Guide

## Prerequisites
- Python 3.10+
- Git
- Optional: Supabase project (PostgreSQL) and Google Cloud project with Gemini access

## Quick Start
1. **Clone and enter the backend project**
   ```bash
   git clone <repo-url>
   cd moniagent/backend
   ```
2. **Create and activate a virtualenv**
   ```bash
   python -m venv .venv
   # Windows
   .venv\Scripts\activate
   # macOS/Linux
   source .venv/bin/activate
   ```
3. **Install dependencies**
   ```bash
   pip install -e .[dev]
   ```
4. **Configure environment**
   ```bash
   cp env_example.txt .env
   # Update SUPABASE_*, DATABASE_URL, JWT_SECRET, GOOGLE_API_KEY etc.
   ```
5. **Run the API**
   ```bash
   uvicorn src.api.main:app --reload
   ```
   - Docs: `http://localhost:8000/docs`
   - Health check: `http://localhost:8000/health`

## Repository Layout
```
backend/
  docs/                 # Guides (architecture, security, API, development)
  src/
    api/                # FastAPI entrypoints and DTOs
    core/               # Config, database, security, LangGraph, cache, scheduler
    models/             # SQLAlchemy models
    services/           # Business logic (OCR, budgeting, AI agent, etc.)
    utils/              # Exceptions, validators, image helpers
  tests/                # Unit, integration, contract suites
  monitoring/           # Observability utilities (WIP)
  uploads/              # Local invoice storage (ignored in git)
  pyproject.toml        # Tooling and entry points
  ruff.toml / mypy.ini  # Linting and type config
```

## Common Commands (run from `backend/`)
- Install: `pip install -e .[dev]`
- Lint: `ruff check .`
- Format: `black .`
- Type check: `mypy src/`
- Tests: `pytest`
- Single test: `pytest tests/unit/test_file.py::test_case`
- Run API: `uvicorn src.api.main:app --reload`

## Database Notes
- `src/core/database.py` builds a connection string from `DATABASE_URL` or Supabase credentials; without those it falls back to `sqlite:///./test.db` (created in the repo root).  
- When running Postgres, provide `SUPABASE_URL` and `SUPABASE_DB_PASSWORD` to form the DSN automatically.  
- Models live under `src/models/` and use SQLAlchemy declarative base; remember to run migrations/DDL externally.
- **Vietnamese Categories**: When a new user registers, 10 Vietnamese system categories and 60-122 keyword-based rules are automatically initialized via `CategoryService.initialize_user_categories()` and `CategorizationService.initialize_vietnamese_categorization_rules()`.
- **LLM Categorization**: Expenses are auto-categorized using Gemini 2.5 Flash with a prompt listing all user's Vietnamese categories. Falls back to keyword-based matching if LLM fails.

## Auth & Environment
- JWT secret is required (`

## Testing
- Unit tests focus on service logic with mocks (see `tests/unit/`).  
- Integration tests target API routes or real DB sessions (`tests/integration/`).  
- Contract/security/performance folders exist for future suites; populate with scenarios before Phase 6.  
- **Vietnamese Categories Testing**: See `tests/integration/test_vietnamese_categories.py` for tests covering:
  - System categories creation and initialization
  - User categories auto-population on registration
  - Categorization rules creation
  - LLM-based categorization flows
- Tips:
  ```bash
  pytest -k ocr_service -vv        # Filter by keyword
  pytest tests/integration/test_vietnamese_categories.py -v  # Vietnamese categories
  pytest --maxfail=1 --disable-warnings
  pytest --cov=src --cov-report=term-missing
  ```