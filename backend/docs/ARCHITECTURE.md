# Architecture Guide

## System Overview
- FastAPI service that ingests invoices, normalises expenses, manages user budgets, and exposes an AI assistant for conversational expense tracking.
- Google Gemini (via LangChain/LangGraph) powers OCR and LLM interactions; `gemini-2.5-flash-lite` handles intent detection for multi-turn confirmation flows.
- Supabase/PostgreSQL stores primary data with an on-disk SQLite fallback for local development.
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
- `expense_processing_service.py` extracts expenses from text or invoices, persists confirmed records, applies corrections, and triggers follow-up work (budget checks, advice). Now includes LLM-based categorization via `categorize_expense_with_llm()`.
- `budget_management_service.py` and `expense_aggregation_service.py` compute budget usage, alerts, and reporting summaries. They operate fully when a SQLAlchemy session is supplied and fall back to deterministic stub data otherwise.
- `financial_advice_service.py` analyses recent spend, derives a spending pattern, and (when available) calls Gemini for tailored advice with safe fallbacks.
- `categorization_service.py` manages user-defined categories, matching rules, keyword-based fallback rules, and feedback learning loops. Also provides `initialize_vietnamese_categorization_rules()` to set up default keyword patterns for new users.
- `category_service.py` handles CRUD operations on categories and provides `initialize_user_categories()` to auto-populate Vietnamese system categories for new users.
- `ai_agent_service.py` glues chat sessions, LangGraph state execution, LLM categorization, corrections, and persistence. Includes `categorize_expense_with_llm()` for intelligent category assignment.

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

### Vietnamese Categories & LLM Categorization
1. **System Categories**: 10 pre-defined Vietnamese categories (Ăn uống, Đi lại, Nhà ở, etc.) are created at migration time as system-wide templates.
2. **User Initialization**: When a new user registers via `POST /v1/auth/register`, the `CategoryService.initialize_user_categories()` is automatically called, copying all system categories to the new user's profile.
3. **LLM-Based Auto-Categorization**: When an expense is extracted (via text input or invoice OCR), the system:
   - Calls `AIAgentService.categorize_expense_with_llm()` with merchant name, amount, and description.
   - Sends a detailed prompt to Gemini 2.5 Flash listing all user categories with Vietnamese names, emojis, and descriptions.
   - Receives a JSON response with `category_id`, `category_name`, and `confidence_score` (0.0-1.0).
   - Falls back to keyword-based rules if LLM categorization fails.
4. **Feedback Loop**: User corrections (via `handle_correction_request`) update the categorization and store feedback for future refinement.

### Conversational Expense Tracking
1. `POST /v1/chat/start` creates a `ChatSession` and returns an onboarding prompt from `AIAgentService.get_initial_message`.
2. `POST /v1/chat/{session_id}/message` stores the user message, forwards it to `LangGraphAIAgent.run`, and appends the assistant reply plus any extracted expense, budget warning, or generated advice.
3. **NEW - Confirmation Flow**:
   - After expense is saved, agent returns response with `asking_confirmation=true` and `saved_expense` details
   - User receives message asking if they want to change the information
   - Frontend displays saved expense details and waits for user confirmation
   - User can respond with "No changes" or corrections like "Thay đổi số tiền thành 50000"
4. **NEW - Correction Processing**:
   - `AIAgentService.detect_update_intent` uses `gemini-2.5-flash-lite` to analyze if user wants updates
   - If user wants corrections, `detect_update_intent` extracts merchant_name, amount, date from message
   - `AIAgentService.handle_update_confirmation` applies corrections via `ExpenseProcessingService.update_expense`
   - Updated expense with confirmation message is returned to user
5. LangGraph nodes call into `ExpenseProcessingService` for extraction and persistence, `BudgetManagementService` for alert checks, and `FinancialAdviceService` for context-aware recommendations.
6. Corrections are parsed in `AIAgentService.handle_correction_request` using a targeted Gemini prompt; confirmed corrections feed back into `ExpenseProcessingService.update_expense`, which records `CategorizationFeedback` when learning is enabled.

## API Layer Updates (`src/api`)

**NEW Response Fields in `/v1/chat/{session_id}/message`**:
- `asking_confirmation` (bool): Indicates agent is asking for confirmation of saved expense
- `saved_expense` (dict): Contains id, merchant_name, amount, date, category_id of the saved expense

The response lifecycle now supports multi-turn confirmation:
1. First response: `asking_confirmation=true`, `saved_expense` populated, `extracted_expense` null
2. User sends correction/confirmation message
3. Second response: `asking_confirmation=false`, confirmation message with updated values

### Budget Monitoring and Reporting
1. Users manage budgets through `