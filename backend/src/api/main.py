from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import ValidationError
import logging

from src.core.config import Settings, configure_logging
from src.utils.exceptions import ApplicationError

# Import all models to ensure SQLAlchemy relationships are initialized
import src.models  # noqa: F401
from src.api.v1.router import router as api_v1_router

configure_logging()
logger = logging.getLogger(__name__)

app = FastAPI(
    title=Settings.app_name,
    description="API for Financial Assistant with OCR and Expense Management",
    version="0.1.0",
)

# CORS configuration - restrict in production
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:8000",
    "https://app.moniagent.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS if Settings.environment != "development" else ["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Add security headers to all responses."""
    response = await call_next(request)
    # Security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = (
        "max-age=31536000; includeSubDomains"
    )
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    return response


@app.exception_handler(ApplicationError)
async def application_error_handler(_: Request, exc: ApplicationError):
    """Handle custom application errors."""
    logger.warning(f"Application error: {exc.error_code} - {exc.message}")
    return JSONResponse(status_code=exc.status_code, content=exc.to_dict())


@app.exception_handler(HTTPException)
async def http_exception_handler(_: Request, exc: HTTPException):
    """Handle FastAPI HTTP exceptions."""
    logger.warning(f"HTTP error: {exc.status_code} - {exc.detail}")
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.exception_handler(ValidationError)
async def validation_exception_handler(_: Request, exc: ValidationError):
    """Handle Pydantic validation errors."""
    logger.warning(f"Validation error: {exc.error_count()} errors")
    return JSONResponse(
        status_code=422,
        content={
            "detail": "Request validation failed",
            "error_code": "VALIDATION_ERROR",
            "errors": exc.errors(),
        },
    )


@app.exception_handler(Exception)
async def generic_exception_handler(_: Request, exc: Exception):
    """Catch-all handler for unexpected errors."""
    logger.error(f"Unexpected error: {type(exc).__name__} - {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "An unexpected error occurred. Please try again later.",
            "error_code": "INTERNAL_ERROR",
        },
    )


@app.get("/")
def read_root():
    """Root endpoint returning API information."""
    return {
        "name": Settings.app_name,
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health")
def health_check():
    """Health check endpoint for monitoring."""
    return {"status": "healthy", "environment": Settings.environment}


# Mount versioned API router
app.include_router(api_v1_router)
