# Architecture Guide: Financial Assistant Backend

## System Overview

The Financial Assistant backend is a FastAPI-based microservice that provides OCR-powered invoice processing, AI-driven expense categorization, and budget management features for a financial tracking application.

### Core Technologies
- **Framework**: FastAPI 0.100+
- **Database**: Supabase (PostgreSQL)
- **Authentication**: JWT tokens with OAuth2
- **AI/ML**: LangChain, LangGraph, Google Gemini 2.5
- **Testing**: pytest with fixtures
- **Deployment**: Docker-ready for Linux servers

---

## Architecture Layers

### 1. API Layer (`src/api/`)
Handles HTTP requests and responses using FastAPI routers.

**Components**:
- `main.py`: FastAPI application instance with middleware setup
- `v1/`: Versioned API endpoints
  - `invoice_router.py`: Invoice upload and OCR processing
  - `category_router.py`: Category management
  - `budget_router.py`: Budget CRUD operations
  - `ai_agent_router.py`: AI-powered features (categorization, advice)
- `schemas/`: Pydantic models for request/response validation

**Key Patterns**:
- Dependency injection for authentication (`get_current_user`)
- Proper HTTP status codes and error handling
- Request/response validation via Pydantic

### 2. Service Layer (`src/services/`)
Business logic implementation with dependency separation.

**Components**:
- `ocr_service.py`: Google Gemini 2.5 Flash integration for invoice OCR
- `invoice_service.py`: Invoice CRUD and processing workflow
- `categorization_service.py`: Expense categorization logic
- `category_service.py`: Category management
- `budget_management_service.py`: Budget tracking and aggregation
- `financial_advice_service.py`: AI-driven financial recommendations
- `expense_aggregation_service.py`: Time-series expense aggregation

**Key Patterns**:
- No direct database access (uses models)
- Stateless design (thread-safe)
- Error handling with appropriate exceptions
- Async-ready for I/O operations

### 3. Model Layer (`src/models/`)
SQLAlchemy ORM models with database schema definitions.

**Components**:
- `user.py`: User account and profile
- `invoice.py`: Invoice metadata and processing state
- `expense.py`: Categorized expenses
- `category.py`: Expense categories with learning
- `budget.py`: User budgets with period tracking
- `ai_interaction.py`: Audit trail for AI operations
- `categorization_feedback.py`: User feedback on categorization
- `expense_categorization_rule.py`: ML-driven categorization rules

**Key Patterns**:
- Relationships defined with proper foreign keys
- Timestamps for audit trail (created_at, updated_at)
- Soft deletes where appropriate
- Unique constraints for data integrity

### 4. Core Layer (`src/core/`)
Infrastructure and cross-cutting concerns.

**Components**:
- `config.py`: Environment configuration, logging setup
- `database.py`: Supabase database connection and session management
- `security.py`: JWT token creation/validation, password hashing
- `ai_config.py`: LangChain/LangGraph initialization

**Key Patterns**:
- Singleton pattern for database and config instances
- Secure credential management via environment variables
- Structured logging for observability

### 5. Utilities (`src/utils/`)
Helper functions and validators.

**Components**:
- `image_utils.py`: Image validation, compression, format detection
- `validators.py`: Custom validation functions
- `helpers.py`: Common utilities

---

## Data Flow

### Invoice Processing Flow
```
1. User uploads invoice image → POST /invoices
2. API layer receives file and validates format
3. Service layer calls OCR service
4. OCR extracts (store_name, date, total_amount)
5. Invoice record stored in database
6. Results returned to frontend
7. User confirms/edits extracted data
8. Updates stored and expense created
```

### Expense Categorization Flow
```
1. Expense created (manual or from invoice)
2. Categorization service analyzes expense
3. AI agent suggests category using LangChain
4. Feedback recorded for model improvement
5. Category assigned to expense
6. Budget aggregation recalculated
```

### Budget Alerts Flow
```
1. Scheduled job runs periodically (via scheduler)
2. Aggregates expenses for period
3. Compares against user budgets
4. Creates alert records if threshold exceeded
5. Alert notification sent to user (via messaging service)
```

---

## Security Architecture

### Authentication & Authorization
- JWT tokens (HS256) for stateless auth
- Token expiration (default: 60 minutes)
- Password hashing with bcrypt (12 rounds)
- Role-based access control (RBAC) ready in models

### Data Protection
- Sensitive data encrypted at rest (Supabase features)
- HTTPS-only in production
- CORS restricted to known frontend domains
- SQL injection prevention via ORM
- Input validation on all endpoints

### Audit Trail
- `ai_interaction` table logs all AI operations
- `categorization_feedback` tracks user corrections
- Timestamps on all sensitive operations
- User ID tracking for accountability

---

## Scalability Considerations

### Database
- Connection pooling via Supabase
- Indexes on frequently queried fields (user_id, created_at)
- Partitioning strategy for expense table (by date)

### API
- Async endpoints for I/O operations
- Rate limiting (to be added)
- Request batching for bulk operations
- Caching layer for frequently accessed data (categories, budgets)

### AI Operations
- Async task queue for long-running OCR jobs
- Result caching to avoid duplicate processing
- Timeout limits for AI operations (default: 30s)

---

## Testing Strategy

### Unit Tests (`tests/unit/`)
- Service layer logic in isolation
- Mocked database and external APIs
- Fast execution (<100ms per test)

### Integration Tests (`tests/integration/`)
- Service layer with real database transactions
- API endpoints with test client
- Database rollback between tests

### Contract Tests (`tests/contract/`)
- External API contracts (Google Gemini, Supabase)
- Request/response format validation
- Error scenario verification

---

## Deployment & Operations

### Environment Configuration
Required `.env` variables:
```
SUPABASE_URL=https://...supabase.co
SUPABASE_ANON_KEY=...
JWT_SECRET=your-long-random-string
GOOGLE_API_KEY=...
```

### Running the Application
```bash
# Development with auto-reload
uvicorn src.api.main:app --reload

# Production with Gunicorn
gunicorn src.api.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

### Monitoring
- Structured logging with JSON output
- Performance metrics for OCR processing
- Error tracking and alerting
- Database query monitoring

---

## Future Enhancements

1. **Notification Service**: Email/SMS alerts for budget overages
2. **Webhook Integration**: Real-time notifications to frontend
3. **Advanced Analytics**: Spending trend analysis
4. **Mobile Optimization**: Mobile-first API design
5. **Multi-currency Support**: International expense tracking
6. **Receipt Storage**: Archive processed invoices
