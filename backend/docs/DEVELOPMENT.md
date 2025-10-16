# Development Guide

## Getting Started

### Prerequisites
- Python 3.10+
- Git
- Supabase account
- Google Cloud API key with Gemini API enabled

### Local Setup

1. **Clone the repository**
```bash
git clone <repository-url>
cd moniagent
```

2. **Create virtual environment**
```bash
cd backend
python -m venv .venv

# On Windows
.venv\Scripts\activate
# On macOS/Linux
source .venv/bin/activate
```

3. **Install dependencies**
```bash
pip install -e ".[dev]"
```

4. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your credentials
```

5. **Run application**
```bash
uvicorn src.api.main:app --reload
```

The API will be available at `http://localhost:8000`
- API docs: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

---

## Project Structure

```
backend/
├── src/
│   ├── api/              # HTTP API layer
│   │   ├── v1/           # V1 endpoints
│   │   └── schemas/      # Pydantic models
│   ├── services/         # Business logic
│   ├── models/           # SQLAlchemy models
│   ├── core/             # Infrastructure
│   └── utils/            # Helpers
├── tests/                # Test suites
│   ├── unit/             # Unit tests
│   ├── integration/       # Integration tests
│   └── contract/         # Contract tests
├── docs/                 # Documentation
├── pyproject.toml        # Project configuration
└── requirements.txt      # Dependencies
```

---

## Code Style & Quality

### Tools
- **Formatter**: Black (line length: 88)
- **Linter**: Ruff
- **Type Checker**: mypy
- **Sorting**: isort

### Running Quality Checks

```bash
# Format code
black src/ tests/

# Sort imports
isort src/ tests/

# Lint code
ruff check src/ tests/ --fix

# Type checking
mypy src/ tests/
```

### Configuration Files
- `pyproject.black`: Black configuration
- `ruff.toml`: Ruff and linter settings
- `mypy.ini`: Type checking rules

---

## Testing

### Running Tests

```bash
# All tests
pytest

# Specific test file
pytest tests/unit/test_ocr_service.py

# Specific test function
pytest tests/unit/test_ocr_service.py::test_extract_invoice_data

# With coverage
pytest --cov=src tests/

# Verbose output
pytest -v

# Show print statements
pytest -s
```

### Test Organization

- **Unit Tests** (`tests/unit/`): Service logic in isolation
  - Mock external dependencies
  - Fast execution
  - Test edge cases

- **Integration Tests** (`tests/integration/`): Components working together
  - Use test database
  - Test workflows
  - Verify error handling

- **Contract Tests** (`tests/contract/`): External API contracts
  - Verify external API expectations
  - Request/response format validation
  - Error scenarios

### Writing Tests

1. **Name convention**: `test_<what_is_being_tested>.py`
2. **Fixture usage**: Use `conftest.py` fixtures for setup
3. **Assertions**: Use descriptive assertion messages
4. **Mocking**: Mock external services, not business logic

Example:
```python
import pytest
from unittest.mock import MagicMock, patch
from src.services.ocr_service import OCRService

@pytest.fixture
def ocr_service():
    return OCRService()

def test_extract_invoice_data(ocr_service):
    """Test invoice data extraction from image."""
    # Arrange
    mock_image = MagicMock()
    
    # Act
    result = ocr_service.extract_invoice_data(mock_image)
    
    # Assert
    assert result['store_name'] == "Expected Store"
    assert result['total_amount'] == 45.99
```

---

## Git Workflow

### Branch Naming
```
feature/US1-invoice-processing
bugfix/JWT-token-expiration
docs/update-api-guide
refactor/extract-common-logic
```

### Commit Messages
```
[US1] Add invoice OCR endpoint
[BUGFIX] Fix password hashing in security module
[DOCS] Update API documentation
[REFACTOR] Extract validation logic into utils
```

### Pull Request Process
1. Create feature branch from `main`
2. Make changes and commit
3. Ensure all tests pass: `pytest`
4. Run quality checks: `black`, `ruff`, `mypy`
5. Create PR with description
6. Address review comments
7. Merge after approval

---

## Common Development Tasks

### Adding a New Endpoint

1. **Create schema** in `src/api/schemas/`:
```python
from pydantic import BaseModel

class MyRequestSchema(BaseModel):
    field: str
    amount: float
```

2. **Create service** in `src/services/`:
```python
class MyService:
    async def process_data(self, data):
        # Business logic
        return result
```

3. **Create route** in `src/api/v1/`:
```python
from fastapi import APIRouter, Depends
from src.core.security import get_current_user

router = APIRouter(prefix="/my-endpoint", tags=["my-feature"])

@router.post("/")
async def create_my_resource(
    request: MyRequestSchema,
    current_user = Depends(get_current_user)
):
    service = MyService()
    return await service.process_data(request)
```

4. **Register router** in `src/api/v1/router.py`:
```python
from .my_router import router as my_router
router.include_router(my_router)
```

5. **Write tests** for all three layers

### Modifying Database Schema

1. Create migration file:
```bash
# Via Supabase CLI
supabase migration new add_new_column_to_users
```

2. Write SQL migration:
```sql
ALTER TABLE users ADD COLUMN new_column VARCHAR(255);
```

3. Apply migration:
```bash
supabase migration up
```

4. Update SQLAlchemy model in `src/models/`

5. Generate TypeScript types (if needed):
```bash
supabase gen types typescript --project-id <project-id>
```

### Debugging

**Debug with print statements:**
```bash
pytest -s test_file.py
```

**Debug with pdb:**
```python
import pdb; pdb.set_trace()  # Breakpoint
```

**Debug specific test:**
```bash
pytest test_file.py::test_function -v -s
```

**View SQL queries (SQLAlchemy logging):**
```python
import logging
logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
```

---

## Environment Variables

### Required
- `SUPABASE_URL`: Supabase project URL
- `SUPABASE_ANON_KEY`: Supabase anonymous key
- `JWT_SECRET`: Secret key for JWT signing
- `GOOGLE_API_KEY`: Google Cloud API key

### Optional
- `SUPABASE_SERVICE_ROLE_KEY`: For admin operations
- `ENV`: Environment (development/production)
- `LOG_LEVEL`: Logging level (DEBUG/INFO/WARNING/ERROR)
- `ACCESS_TOKEN_EXPIRE_MINUTES`: JWT expiration time

See `.env.example` for template

---

## Performance Profiling

### Profile endpoint speed
```python
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()
# ... code to profile ...
profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(10)
```

### Check database query performance
```python
from sqlalchemy import event
from src.core.database import engine

@event.listens_for(engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    print(f"Query: {statement}")
    print(f"Parameters: {parameters}\n")
```

---

## Troubleshooting

### Common Issues

**ImportError: No module named 'src'**
- Ensure you're in the `backend/` directory
- Ensure virtual environment is activated
- Run `pip install -e .`

**JWT_SECRET not configured**
- Add `JWT_SECRET` to `.env` file
- Restart the application

**Supabase connection timeout**
- Check internet connection
- Verify `SUPABASE_URL` is correct
- Check Supabase project is active

**Tests failing with database errors**
- Ensure test database is accessible
- Check test fixtures in `conftest.py`
- Run `pytest -v -s` for detailed output

---

## Useful Commands

```bash
# Run tests with coverage report
pytest --cov=src --cov-report=html tests/

# Format and lint all code
black src/ tests/ && ruff check src/ tests/ --fix && isort src/ tests/

# Run type checking
mypy src/ tests/

# Start development server with debugging
uvicorn src.api.main:app --reload --log-level debug

# List all routes
python -c "from src.api.main import app; [print(route.path) for route in app.routes]"
```

---

## Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Supabase Documentation](https://supabase.com/docs)
- [Google Gemini API](https://ai.google.dev/docs)
- [LangChain Documentation](https://python.langchain.com/)
- [pytest Documentation](https://docs.pytest.org/)
