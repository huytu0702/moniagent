import { apiClient } from './client';
import { Category, CategoryListResponse } from './types';

export const categoryAPI = {
  /**
   * Get all categories for the current user
   */
  list: async (token: string): Promise<CategoryListResponse> => {
    const response = await apiClient.get<Category[] | CategoryListResponse>('/categories', token);
    // Handle both array response and object with categories property
    if (Array.isArray(response)) {
      return { categories: response };
    }
    return { categories: response?.categories || [] };
  },

  /**
   * Get a single category by ID
   */
  get: async (categoryId: string, token: string): Promise<Category> => {
    return apiClient.get<Category>(`/categories/${categoryId}`, token);
  },
};
