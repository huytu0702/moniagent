# Security Guide

## Authentication & Session Management
- `src/core/security.py` issues HS256 JWTs via `create_access_token`; the default expiry is 60 minutes (`DEFAULT_ACCESS_TOKEN_EXPIRE_MINUTES`). Store tokens in HTTP-only, Secure cookies on the client whenever possible.
- Passwords are hashed with bcrypt (12 rounds). Always call `hash_password` and `verify_password`; never store plaintext or truncated hashes.
- `OAuth2PasswordBearer` is registered with `tokenUrl="token"`. In production UIs, point it to `/v1/auth/login`. The login endpoint expects `application/x-www-form-urlencoded` credentials (`username`, `password`).
- `get_current_user` enforces authentication for every router except `/auth/*`. In development (`ENV=development`) the bearer token `mock-token-for-development` resolves to a synthetic user to simplify local testing; disable this shortcut in staging/production.

## Authorisation & Ownership
- API routers verify ownership before returning or mutating user data. Examples:  
  - `invoice_router.get_invoice` checks `invoice['user_id'] != current_user.id`.  
  - `expense_router.get_expense_by_id` raises `403` when a user attempts to load another user's expense.  
  - Budget and category operations re-use the authenticated user id supplied by `get_current_user`.
- Persisted models (SQLAlchemy) enforce foreign keys: Expense <-> User/Category, Invoice <-> User.

## Transport & Headers
- `src/api/main.py` configures CORS to allow any origin in development and a curated allowlist otherwise. Review `ALLOWED_ORIGINS` before release.
- HTTP middleware injects security headers on every response:  
  `X-Content-Type-Options=nosniff`, `X-Frame-Options=DENY`, `X-XSS-Protection=1; mode=block`, `Strict-Transport-Security` (one year), and a Content Security Policy for the docs UI. Ensure TLS is enabled so HSTS is effective.

## Input Validation & Sanitisation
- Pydantic schemas cover request validation; shared validators live in `src/api/validation.py` and `src/utils/validators.py` (email, password, UUID, amount, etc).
- Invoice uploads are limited to JPEG/PNG through MIME checks in `invoice_router.process_invoice`; extend this with file-size limits and content sniffing if accepting user uploads in production.
- Chat corrections are parsed by a Gemini prompt that requests JSON only; responses strip markdown fences and validate with `json.loads`.
- Use `sanitize_text` and `sanitize_filename` helpers when dealing with user-provided strings outside Pydantic models (e.g., ad-hoc scripts or background workers).

## Data Protection
- `src/core/config.py` reads secrets from environment variables. Never commit `.env` files containing production credentials.
- `src/core/database.py` prefers `DATABASE_URL` or builds a Supabase DSN (with connection pooling). Without env vars it falls back to `sqlite:///./test.db`; do not run production workloads on the default SQLite file.
- Supabase credentials: use the service role key server-side only, never expose to the front end. Rotate keys on suspicion of leakage.
- Sensitive fields (password hashes, tokens) are excluded from API responses. Review new schemas carefully to avoid accidental data leaks.

## External Integrations
- **Google Gemini**: API key retrieved from `GOOGLE_API_KEY`. Calls are wrapped with error handling; malformed replies trigger `ValueError` and return 400/500 to the client. Consider adding request quotas and fallbacks when rate-limited.
- **LangGraph / LangChain**: Tool bindings call deterministic services only; avoid exposing raw user input to the LLM without sanitisation. Add content filtering if dealing with PII or financial account numbers.
- **Supabase**: Database interactions rely on SQLAlchemy ORM queries. Enable Row Level Security (RLS) policies in Supabase for an extra protection layer.

## Logging & Monitoring
- `configure_logging` sets global logging according to `LOG_LEVEL`. Sensitive data (passwords, tokens, invoice contents) must never be logged; current code only logs identifiers and status messages.
- Gemeni/OCR logs truncate content to avoid sending entire invoices to logs. Continue redacting or hashing identifiers if detailed diagnostics are required.
- Instrument important flows (invoice uploads, chat confirmation) with structured logs that include request ids or session ids for traceability.

## File Handling
- Uploaded invoices are streamed; `InvoiceService` should store files outside the web root (currently `backend/uploads`). Ensure this directory is excluded from static serving and backed up securely.
- Add anti-malware scanning or a proxy service before persisting user files in production.

## Development vs Production
- Disable debug logging and the mock JWT token when deploying outside development.  
- Ensure `.env` files are environment-specific; prefer secret managers (Supabase, AWS Secrets Manager, etc.) for production credentials.
- Replace the placeholder return values in budget endpoints and chat confirm routes before launch; they are currently informational only and may leak deterministic demo data.

## Hardening Checklist
- [ ] Enforce HTTPS and verify HSTS headers in production.  
- [ ] Rotate `JWT_SECRET`, Supabase keys, and `GOOGLE_API_KEY` regularly.  
- [ ] Implement refresh tokens or short-lived access tokens plus reauth if session duration requirements extend beyond 60 minutes.  
- [ ] Add rate limiting (login, invoice upload, chat) via API gateway or custom middleware.  
- [ ] Enable alerting on authentication failures, unusual spend extraction, and OCR errors.  
- [ ] Back up the production database and perform periodic restore drills.  
- [ ] Run dependency vulnerability scans (`pip-audit`, GitHub dependabot) monthly.  
- [ ] Conduct penetration testing focusing on file uploads, chat prompt injection, and JWT tampering.  
- [ ] Ensure Supabase RLS rules match API ownership checks (defence in depth).

## Future Improvements
- Introduce CSRF protection if session cookies are used.  
- Add account locking or exponential backoff on repeated authentication failures.  
- Persist full audit trails for expense corrections and AI-suggested actions.  
- Extend chat safety with prompt shields or moderation endpoints before forwarding to Gemini.  
- Capture structured metrics (latency, OCR success rate, LLM token usage) for proactive monitoring.
