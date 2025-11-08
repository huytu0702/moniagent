const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/v1';

class APIError extends Error {
  constructor(
    public status: number,
    public message: string,
    public errorCode?: string
  ) {
    super(message);
    this.name = 'APIError';
  }
}

class APIClient {
  private baseURL: string;

  constructor(baseURL: string = API_BASE_URL) {
    this.baseURL = baseURL;
  }

  private getHeaders(token?: string): HeadersInit {
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
    };
    
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    
    return headers;
  }

  private async handleResponse<T>(response: Response): Promise<T> {
    if (!response.ok) {
      const error = await response.json().catch(() => ({
        detail: 'An error occurred',
      }));
      
      // Handle different error formats
      let errorMessage = 'An error occurred';
      
      if (typeof error.detail === 'string') {
        errorMessage = error.detail;
      } else if (Array.isArray(error.detail)) {
        // FastAPI validation errors format: [{type, loc, msg, input}]
        errorMessage = error.detail
          .map((err: any) => err.msg || JSON.stringify(err))
          .join(', ');
      } else if (error.message) {
        errorMessage = error.message;
      } else if (error.detail) {
        errorMessage = JSON.stringify(error.detail);
      }
      
      throw new APIError(
        response.status,
        errorMessage,
        error.error_code
      );
    }

    return response.json();
  }

  async get<T>(endpoint: string, token?: string, options?: RequestInit): Promise<T> {
    const response = await fetch(`${this.baseURL}${endpoint}`, {
      method: 'GET',
      headers: this.getHeaders(token),
      ...options,
      // Next.js 15 fetch options
      cache: options?.cache || 'no-store',
    });

    return this.handleResponse<T>(response);
  }

  async post<T>(endpoint: string, data: any, token?: string, options?: RequestInit): Promise<T> {
    const response = await fetch(`${this.baseURL}${endpoint}`, {
      method: 'POST',
      headers: this.getHeaders(token),
      body: JSON.stringify(data),
      ...options,
      // Next.js 15 fetch options
      cache: options?.cache || 'no-store',
    });

    return this.handleResponse<T>(response);
  }

  async postForm<T>(endpoint: string, data: Record<string, string>, token?: string, options?: RequestInit): Promise<T> {
    const formData = new URLSearchParams();
    Object.entries(data).forEach(([key, value]) => {
      formData.append(key, value);
    });

    const headers: HeadersInit = {
      'Content-Type': 'application/x-www-form-urlencoded',
    };
    
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(`${this.baseURL}${endpoint}`, {
      method: 'POST',
      headers,
      body: formData.toString(),
      ...options,
      cache: options?.cache || 'no-store',
    });

    return this.handleResponse<T>(response);
  }

  async put<T>(endpoint: string, data: any, token?: string, options?: RequestInit): Promise<T> {
    const response = await fetch(`${this.baseURL}${endpoint}`, {
      method: 'PUT',
      headers: this.getHeaders(token),
      body: JSON.stringify(data),
      ...options,
      cache: options?.cache || 'no-store',
    });

    return this.handleResponse<T>(response);
  }

  async delete<T>(endpoint: string, token?: string, options?: RequestInit): Promise<T> {
    const response = await fetch(`${this.baseURL}${endpoint}`, {
      method: 'DELETE',
      headers: this.getHeaders(token),
      ...options,
      cache: options?.cache || 'no-store',
    });

    return this.handleResponse<T>(response);
  }
}

export const apiClient = new APIClient();
export { APIError };
