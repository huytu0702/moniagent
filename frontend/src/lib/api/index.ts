export { authAPI } from './auth';
export { chatAPI } from './chat';

export { apiClient, APIError } from './client';

export * from './types';

// Re-export error handling utilities for convenience
export { getErrorMessage, handleAPIError, logError } from '../error-handler';
