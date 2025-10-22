# Architecture Guide

## System Overview
- FastAPI service that ingests invoices, normalises expenses, manages user budgets, and exposes an AI assistant for conversational expense tracking.
- Google Gemini (via LangChain/LangGraph) powers OCR and LLM interactions; Supabase/PostgreSQL stores primary data with an on-disk SQLite fallback for local development.
- JWT-based auth wraps all v1 endpoints except `/auth/*`; custom exceptions and structured logging keep error handling consistent.

## Technology Stack
- Python 3.10+, FastAPI, SQLAlchemy, Supabase client SDK.
- Google Generative AI (Gemini 2.5) through LangChain / LangGraph for agent flows.
- Pydantic models for IO schemas, pytest/pytest-asyncio for tests, Ruff + Black + mypy for quality gates.

## Repository Layout
```
backend/
  docs/                   # Architecture, security, API, development guides
  src/
    api/
      main.py             # App factory, middleware, global exception handlers
      validation.py       # Pydantic helpers and sanitizers
      schemas/            # Request/response DTOs
      v1/
        router.py         # Aggregates versioned routers
        auth_router.py    # Register/login
        invoice_router.py # OCR-driven invoice ingestion
        expense_router.py # Expense CRUD and corrections
        category_router.py# Categories + rule management
        budget_router.py  # Budgets + spending summary
        chat_router.py    # Chat/LangGraph orchestration
        ai_agent_router.py# Financial advice endpoint
    core/
      config.py           # Environment-driven settings + logging
      database.py         # SQLAlchemy engine + Supabase client helpers
      security.py         # JWT, bcrypt, request identity helpers
      ai_config.py        # Gemini client bootstrap
      langgraph_agent.py  # LangGraph state machine
      cache.py            # In-memory TTL cache utilities
      scheduler.py        # Async task scheduler stubs
    models/               # SQLAlchemy models (User, Expense, Invoice, Budget, ...)
    services/             # Business logic modules (OCR, AI agent, budgeting, ...)
    utils/                # Exceptions, validators, image utilities
```

## Layer Breakdown

### API Layer (`src/api`)
- `main.py` wires CORS, security headers, logging, and global exception handlers for `ApplicationError`, `HTTPException`, `ValidationError`, and unexpected errors.
- `validation.py` centralises reusable Pydantic request validators and sanitisation helpers.
- `v1/router.py` applies the `/v1` prefix and mounts each feature router. Authentication (`get_current_user`) is enforced on every router except `auth`.
- Feature routers encapsulate specific capabilities: invoices (OCR upload, listing), expenses (manual entry and corrections), categories and rule management, budgets/spending, chat sessions, and AI financial advice.
- `schemas/` contains DTOs consumed by the routers; additional lightweight models live inside some routers (for example `expense_router.py`).

### Services (`src/services`)
- `invoice_service.py` coordinates OCR ingestion, persistence, and querying of invoices.
- `ocr_service.py` streams invoice images to Gemini 2.5 Flash, normalises the JSON payload, and handles markdown wrapped results.
- `expense_processing_service.py` extracts expenses from text or invoices, persists confirmed records, applies corrections, and triggers follow-up work (budget checks, advice).
- `budget_management_service.py` and `expense_aggregation_service.py` compute budget usage, alerts, and reporting summaries. They operate fully when a SQLAlchemy session is supplied and fall back to deterministic stub data otherwise.
- `financial_advice_service.py` analyses recent spend, derives a spending pattern, and (when available) calls Gemini for tailored advice with safe fallbacks.
- `categorization_service.py` and `category_service.py` manage user-defined categories, matching rules, and feedback learning loops.
- `ai_agent_service.py` glues chat sessions, LangGraph state execution, corrections, and persistence.

### Models (`src/models`)
- SQLAlchemy declarative models for users, invoices, expenses, budgets, chat sessions/messages, categorisation rules, and feedback.
- Each model exposes helper methods (for example `to_dict`) and keeps created/updated timestamps for audit trails.
- Relationships capture ownership: user <-> categories/expenses/budgets, expense <-> feedback/rules.

### Core Infrastructure (`src/core`)
- `config.py` exposes immutable `Settings` with env-driven defaults plus `configure_logging`.
- `database.py` builds a SQLAlchemy engine from `DATABASE_URL` or Supabase credentials, yielding a PostgreSQL DSN; it falls back to `sqlite:///./test.db` for local runs and exposes a cached Supabase client when direct REST/RPC calls are needed.
- `security.py` handles bcrypt hashing, JWT issuance/validation, and the FastAPI dependency `get_current_user`, including a guarded `mock-token-for-development` path for local runs.
- `langgraph_agent.py` defines a LangGraph `StateGraph` that orchestrates extraction, confirmation, budget checks, and follow-up LLM replies; tools bridge to `ExpenseProcessingService`, `BudgetManagementService`, and `FinancialAdviceService`.
- `cache.py` supplies an in-memory TTL cache and decorators for hot-path responses.
- `scheduler.py` describes a cooperative async scheduler with placeholder budget alert and aggregation tasks (ready for background processing integration).

### Utilities (`src/utils`)
- `exceptions.py` provides structured domain exceptions which bubble through FastAPI handlers cleanly.
- `validators.py` offers reusable validation helpers for emails, passwords, monetary values, dates, and enums.
- `image_utils.py` covers invoice pre-processing utilities used by OCR flows.

## Key Workflows

### Invoice -> Expense
1. `POST /v1/invoices/process` validates MIME type and streams the upload to `InvoiceService.process_invoice_upload`.
2. `InvoiceService` leverages `OCRService.process_invoice` (Gemini 2.5 Flash) to extract merchant, total, and date values, then creates or updates an `Invoice` record.
3. The API responds with `InvoiceResponse`; downstream flows (manual confirmation or chat) can transform the invoice into an expense entry.

### Conversational Expense Tracking
1. `POST /v1/chat/start` creates a `ChatSession` and returns an onboarding prompt from `AIAgentService.get_initial_message`.
2. `POST /v1/chat/{session_id}/message` stores the user message, forwards it to `LangGraphAIAgent.run`, and appends the assistant reply plus any extracted expense, budget warning, or generated advice.
3. LangGraph nodes call into `ExpenseProcessingService` for extraction and persistence, `BudgetManagementService` for alert checks, and `FinancialAdviceService` for context-aware recommendations.
4. Corrections are parsed in `AIAgentService.handle_correction_request` using a targeted Gemini prompt; confirmed corrections feed back into `ExpenseProcessingService.update_expense`, which records `CategorizationFeedback` when learning is enabled.

### Budget Monitoring and Reporting
1. Users manage budgets through `POST /v1/budgets`, `PUT /v1/budgets/{id}`, and `DELETE /v1/budgets/{id}`.
2. `BudgetManagementService.check_budget_status` powers `GET /v1/budgets/check/{category_id}`, projecting remaining spend and flagging thresholds.
3. `ExpenseAggregationService.get_spending_summary` backs `GET /v1/spending/summary`, aggregating real data when a DB session is supplied and falling back to deterministic fixtures during local testing.
4. `scheduler.py` describes reusable tasks (`BudgetAlertTask`, `ExpenseAggregationTask`) that can run in the background once wired to an event loop or worker.

### Categorisation & Feedback Loop
1. Expense suggestions (`POST /v1/categories/suggest`) use `CategorizationService.suggest_category` to match user-defined rules and heuristics.
2. Confirmations or corrections (`POST /v1/categories/confirm` and expense updates) persist `CategorizationFeedback`, closing the feedback loop for future recommendations.
3. Rule CRUD endpoints expose fine-grained control over keyword/regex/exact match strategies per user.

## External Integrations
- **Supabase/PostgreSQL**: primary persistence via SQLAlchemy; environment variables (`SUPABASE_URL`, `SUPABASE_DB_PASSWORD`) produce a connection string with connection pooling and SQL echo for debug mode.
- **Google Generative AI (Gemini)**: OCR and LLM tasks run through `google-generativeai` clients; API keys are loaded lazily to keep startup flexible.
- **LangChain / LangGraph**: The agent graph composes deterministic tools with generative outputs, modelling expense extraction and advice as state transitions rather than ad-hoc prompt chains.

## Error Handling & Resilience
- `ApplicationError` hierarchy maps domain failures to typed HTTP responses; FastAPI exception handlers return canonical `{detail, error_code}` payloads.
- OCR and AI interactions sanitise markdown-wrapped JSON before parsing, reducing malformatted response risk.
- Budget, aggregation, and advice services provide deterministic fallbacks when external services or DB sessions are unavailable, keeping API responses predictable during local development.

## Known Gaps & Next Steps
- Several endpoints (`GET /v1/budgets/{id}`, chat correction flows) still return placeholder data until the persistence layer is finalised.
- Scheduler tasks are defined but not yet hooked to a long-running worker or FastAPI lifespan event.
- Rate limiting, notification delivery, and webhook callbacks are not implemented; the architecture leaves space to add them behind `core` utilities.
- Additional observability (structured logs to a sink, tracing) and more comprehensive automated tests are recommended as the service matures.
