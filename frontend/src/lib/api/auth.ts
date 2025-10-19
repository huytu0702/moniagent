import { apiClient } from './client';
import { LoginRequest, RegisterRequest, AuthResponse, User, UserRegisterResponse } from './types';

export const authAPI = {
  /**
   * Đăng nhập
   * Backend uses OAuth2PasswordRequestForm which requires form-data
   */
  login: async (data: LoginRequest): Promise<AuthResponse> => {
    const response = await apiClient.postForm<AuthResponse>('/auth/login', {
      username: data.email,
      password: data.password,
    });
    
    // Backend doesn't return expires_in, so we set default to 60 minutes (3600 seconds)
    if (!response.expires_in) {
      response.expires_in = 3600; // 60 minutes in seconds
    }
    
    return response;
  },

  /**
   * Đăng ký tài khoản mới
   */
  register: async (data: RegisterRequest): Promise<UserRegisterResponse> => {
    return apiClient.post<UserRegisterResponse>('/auth/register', data);
  },
};
