/**
 * Utility functions for handling errors consistently across the app
 */

/**
 * Extract a readable error message from any error type
 * @param error - The error object (can be Error, string, or unknown)
 * @param fallbackMessage - Default message if no error message can be extracted
 * @returns A user-friendly error message string
 */
export function getErrorMessage(error: unknown, fallbackMessage = "An unexpected error occurred"): string {
  // If it's already a string, return it
  if (typeof error === 'string') {
    return error;
  }

  // If it's an Error object or has a message property
  if (error && typeof error === 'object') {
    const err = error as any;
    
    // Check for message property
    if (typeof err.message === 'string') {
      return err.message;
    }

    // Check for detail property (FastAPI error format)
    if (err.detail) {
      if (typeof err.detail === 'string') {
        return err.detail;
      }
      
      // Handle validation errors array
      if (Array.isArray(err.detail)) {
        return err.detail
          .map((e: any) => {
            if (typeof e === 'string') return e;
            if (e.msg) return e.msg;
            return JSON.stringify(e);
          })
          .join(', ');
      }
    }

    // If it's a fetch/network error
    if (err.name === 'TypeError' && err.message.includes('fetch')) {
      return 'Network error. Please check your connection.';
    }
  }

  // Return fallback message
  return fallbackMessage;
}

/**
 * Log error to console (in development) or error reporting service (in production)
 * @param error - The error to log
 * @param context - Additional context about where the error occurred
 */
export function logError(error: unknown, context?: string): void {
  if (process.env.NODE_ENV === 'development') {
    console.error(context ? `[${context}]` : '[Error]', error);
  } else {
    // In production, you might want to send to an error tracking service
    // e.g., Sentry, LogRocket, etc.
    console.error(context ? `[${context}]` : '[Error]', getErrorMessage(error));
  }
}

/**
 * Handle API errors and return a user-friendly message
 * @param error - The API error
 * @param customMessages - Custom messages for specific error codes
 * @returns A user-friendly error message
 */
export function handleAPIError(
  error: unknown,
  customMessages?: Record<number, string>
): string {
  if (error && typeof error === 'object') {
    const err = error as any;
    
    // Check for HTTP status code
    if (err.status && customMessages && customMessages[err.status]) {
      return customMessages[err.status];
    }

    // Handle common HTTP status codes
    switch (err.status) {
      case 400:
        return getErrorMessage(error, 'Invalid request. Please check your input.');
      case 401:
        return 'Unauthorized. Please log in again.';
      case 403:
        return 'You do not have permission to perform this action.';
      case 404:
        return 'The requested resource was not found.';
      case 409:
        return getErrorMessage(error, 'A conflict occurred. This resource may already exist.');
      case 422:
        return getErrorMessage(error, 'Validation error. Please check your input.');
      case 429:
        return 'Too many requests. Please try again later.';
      case 500:
        return 'Server error. Please try again later.';
      case 503:
        return 'Service unavailable. Please try again later.';
    }
  }

  return getErrorMessage(error, 'An unexpected error occurred. Please try again.');
}
