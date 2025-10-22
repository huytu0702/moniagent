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

## Auth & Environment
- JWT secret is required (`JWT_SECRET`).  
- Development shortcut: requests authenticated with bearer token `mock-token-for-development` resolve to a stub user when `ENV=development`.  
- CORS defaults to allow all origins in development and a restricted list otherwise (see `src/api/main.py`).

## Quality Gates
- **Ruff** handles linting and import sorting (configured via `ruff.toml`).  
- **Black** formats with line length 88 (configured via `pyproject.black`).  
- **mypy** enforces typing in `src/` (configuration in `mypy.ini`).  
- Optional pre-commit hooks are defined in `.pre-commit-config.yaml`; enable via `pre-commit install`.

## Testing
- Unit tests focus on service logic with mocks (see `tests/unit/`).  
- Integration tests target API routes or real DB sessions (`tests/integration/`).  
- Contract/security/performance folders exist for future suites; populate with scenarios before Phase 6.  
- Tips:
  ```bash
  pytest -k ocr_service -vv        # Filter by keyword
  pytest --maxfail=1 --disable-warnings
  pytest --cov=src --cov-report=term-missing
  ```

## Debugging & Tooling
- Enable SQL echo logs by exporting `SQLALCHEMY_ECHO=1` or editing `database.py` when running locally.  
- To inspect routes quickly:
  ```bash
  python -c "from src.api.main import app; [print(r.path) for r in app.routes]"
  ```
- For ad-hoc LangGraph runs, instantiate `LangGraphAIAgent` with a session from `get_db()` inside a REPL or notebook.

## Workflows & Tips
- Use `ExpenseProcessingService` or `BudgetManagementService` directly in tests by creating a session fixture (see `tests/conftest.py`).  
- Invoice uploads expect JPEG/PNG and stream data through `OCRService`; when running without a Gemini key, mock the service to keep tests deterministic.  
- Several services (budgets, aggregation, advice) fall back to canned data if `db_session` is omitted; use this behaviour for quick demos but prefer real sessions for integration tests.

## Deployment Reminders
- Compile environment variables for each environment (`.env.production`, `.env.staging`, etc.).  
- Configure HTTPS termination and ensure the `Strict-Transport-Security` header from `src/api/main.py` remains in place.  
- Attach background workers or lifespan startups if you plan to enable tasks defined in `scheduler.py`.
