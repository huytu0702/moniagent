from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from src.core.config import Settings, configure_logging
from src.api.v1.router import router as api_v1_router


configure_logging()

app = FastAPI(
    title=Settings.app_name,
    description="API for Financial Assistant with OCR and Expense Management",
    version="0.1.0",
)

# Basic CORS for development; tighten in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    # Minimal security headers; extend as needed
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("X-XSS-Protection", "1; mode=block")
    return response


@app.exception_handler(HTTPException)
async def http_exception_handler(_: Request, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.exception_handler(ValidationError)
async def validation_exception_handler(_: Request, exc: ValidationError):
    return JSONResponse(status_code=422, content={"detail": exc.errors()})

@app.get("/")
def read_root():
    return {"Hello": "World"}


# Mount versioned API router (empty for now; endpoints will be added per stories)
app.include_router(api_v1_router)

@app.get("/health")
def health_check():
    return {"status": "healthy"}