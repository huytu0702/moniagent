"""
Centralized exception definitions for consistent error handling across the application.
"""


class ApplicationError(Exception):
    """Base exception for all application errors."""

    def __init__(self, message: str, error_code: str = None, status_code: int = 500):
        """
        Initialize an application error.

        Args:
            message: Human-readable error message
            error_code: Machine-readable error code for client handling
            status_code: HTTP status code to return to client
        """
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.status_code = status_code
        super().__init__(self.message)

    def to_dict(self):
        """Convert exception to dictionary for JSON response."""
        return {
            "detail": self.message,
            "error_code": self.error_code,
        }


class ValidationError(ApplicationError):
    """Raised when input validation fails."""

    def __init__(self, message: str, error_code: str = None):
        super().__init__(message, error_code or "VALIDATION_ERROR", 422)


class AuthenticationError(ApplicationError):
    """Raised when authentication fails."""

    def __init__(self, message: str = "Authentication failed", error_code: str = None):
        super().__init__(message, error_code or "AUTH_ERROR", 401)


class AuthorizationError(ApplicationError):
    """Raised when user lacks permission."""

    def __init__(
        self, message: str = "Insufficient permissions", error_code: str = None
    ):
        super().__init__(message, error_code or "PERMISSION_DENIED", 403)


class NotFoundError(ApplicationError):
    """Raised when resource is not found."""

    def __init__(self, message: str, error_code: str = None):
        super().__init__(message, error_code or "NOT_FOUND", 404)


class ConflictError(ApplicationError):
    """Raised when resource already exists or conflict occurs."""

    def __init__(self, message: str, error_code: str = None):
        super().__init__(message, error_code or "CONFLICT", 409)


class InvoiceProcessingError(ApplicationError):
    """Raised when invoice processing fails."""

    def __init__(self, message: str, error_code: str = None):
        super().__init__(message, error_code or "INVOICE_ERROR", 400)


class OCRError(ApplicationError):
    """Raised when OCR processing fails."""

    def __init__(self, message: str, error_code: str = None):
        super().__init__(message, error_code or "OCR_ERROR", 500)


class CategorizationError(ApplicationError):
    """Raised when categorization fails."""

    def __init__(self, message: str, error_code: str = None):
        super().__init__(message, error_code or "CATEGORIZATION_ERROR", 400)


class BudgetError(ApplicationError):
    """Raised when budget operations fail."""

    def __init__(self, message: str, error_code: str = None):
        super().__init__(message, error_code or "BUDGET_ERROR", 400)


class DatabaseError(ApplicationError):
    """Raised when database operations fail."""

    def __init__(self, message: str, error_code: str = None):
        super().__init__(message, error_code or "DATABASE_ERROR", 500)


class ExternalServiceError(ApplicationError):
    """Raised when external API calls fail."""

    def __init__(self, message: str, error_code: str = None):
        super().__init__(message, error_code or "EXTERNAL_SERVICE_ERROR", 503)
