Dependency Audit (Phase 6)

Reviewed key dependencies in backend/requirements.txt:

- fastapi: Actively maintained, security-conscious. Keep updated.
- uvicorn: Update regularly; avoid debug auto-reload in production.
- pydantic: v2+ has stricter validation; no known critical CVEs at time of writing.
- langchain/langgraph: Indirect network calls; ensure timeouts and input sanitization.
- supabase: Server keys kept only on backend; verify RLS policies.
- google-generativeai: API key via env; rate-limit and set timeouts.
- pillow: Past CVEs; keep up-to-date (>=10). Validate images before processing.
- bcrypt/PyJWT: Keep patched; use strong hashing rounds; verify token algorithms.
- python-multipart: For uploads; validate size and content type.

Recommendations:

- Run `pip list --outdated` monthly and update.
- Consider integrating `pip-audit` in CI to catch vulnerabilities.
- Lock dependencies with hashed constraints for production deployments.
