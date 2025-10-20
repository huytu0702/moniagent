# Agent Guidelines for Moniagent

## Build/Lint/Test Commands
- Install: `pip install -e .[dev]` (from backend/)
- Run app: `uvicorn src.api.main:app --reload` (from backend/)
- Run all tests: `pytest` (from backend/)
- Run single test: `pytest tests/unit/test_file.py::test_function` (from backend/)
- Lint: `ruff check .` (from backend/)
- Format: `black .` (from backend/)
- Type check: `mypy src/` (from backend/)

## Architecture and Codebase Structure
- **Backend**: FastAPI microservice in Python 3.10+ with Supabase (PostgreSQL), JWT auth, OCR via Google Gemini 2.5, AI categorization via LangChain/LangGraph.
- **Key directories**: `backend/src/` (api, core, models, services, utils), `backend/tests/` (unit, integration, contract, security, performance), `specs/` (feature specs and plans).
- **Databases**: Supabase for user/expense data, file uploads for invoices.
- **APIs**: RESTful v1 endpoints for invoices, expenses, categories, budgets, AI agent chat.

## Code Style Guidelines
- **Python**: 3.10+, follow PEP 8, line length 88 (Black).
- **Imports**: Sorted with isort (via Ruff), no unused imports.
- **Formatting**: Black for auto-formatting, double quotes, spaces for indent.
- **Types**: Use mypy for static typing, disallow untyped defs in src/.
- **Naming**: snake_case for functions/variables, PascalCase for classes, UPPER_CASE for constants.
- **Error handling**: Raise custom exceptions from utils/exceptions.py, log errors with structured logging.
- **Async**: Use async/await for I/O operations, pytest-asyncio for tests.
