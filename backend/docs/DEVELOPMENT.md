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
- **Confirmation Flow** (NEW): After saving an expense, the agent asks for confirmation before returning to the user. Users can approve or provide corrections (merchant name, amount, date), which are detected using `gemini-2.5-flash-lite` model.

## Auth & Environment
- JWT secret is required (`JWT_SECRET` env var)
- Mock token for development: `mock-token-for-development` resolves to a synthetic user in development mode

## Testing
- Unit tests focus on service logic with mocks (see `tests/unit/`).  
- Integration tests target API routes or real DB sessions (`tests/integration/`).  
- Contract/security/performance folders exist for future suites; populate with scenarios before Phase 6.  
- **Vietnamese Categories Testing**: See `tests/integration/test_vietnamese_categories.py` for tests covering:
  - System categories creation and initialization
  - User categories auto-population on registration
  - Categorization rules creation
  - LLM-based categorization flows
- **Confirmation Flow Testing** (NEW): See `tests/unit/test_confirmation_flow.py` for comprehensive tests covering:
  - LangGraph confirmation nodes (`ask_confirmation`, `detect_update_intent`, `process_update`)
  - Intent detection with keyword fallback
  - Multi-turn conversation with corrections
  - Budget warnings and financial advice during confirmation
  - Tests include:
    ```bash
    pytest tests/unit/test_confirmation_flow.py -v
    pytest tests/unit/test_confirmation_flow.py::TestConfirmationFlow::test_handle_update_confirmation_with_update -v
    pytest tests/unit/test_confirmation_flow.py::TestLangGraphConfirmationNodes -v
    ```
- Tips:
  ```bash
  pytest -k ocr_service -vv        # Filter by keyword
  pytest tests/integration/test_vietnamese_categories.py -v  # Vietnamese categories
  pytest tests/unit/test_confirmation_flow.py -v  # Confirmation flow
  pytest --maxfail=1 --disable-warnings
  pytest --cov=src --cov-report=term-missing
  ```

## Manual Testing Confirmation Flow (Local)
1. Start API: `uvicorn src.api.main:app --reload`
2. Register user: `POST /v1/auth/register` with email/password
3. Start chat: `POST /v1/chat/start`
4. Send expense message: `POST /v1/chat/{session_id}/message` with text like "Tôi mua cà phê 25000đ tại Starbucks"
5. Agent returns with `asking_confirmation=true` and saved_expense details
6. Send confirmation: `POST /v1/chat/{session_id}/message` with "Không" (no changes) or "Thay đổi số tiền thành 50000" (corrections)
7. Agent processes intent detection and returns final confirmation message