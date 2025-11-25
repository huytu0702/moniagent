import { apiClient } from './client';
import {
  Budget,
  BudgetListResponse,
  CreateBudgetRequest,
  UpdateBudgetRequest
} from './types';

export const budgetAPI = {
  /**
   * Get all budgets for the current user
   */
  list: async (token: string): Promise<Budget[]> => {
    const response = await apiClient.get<Budget[] | BudgetListResponse>('/budgets', token);
    // Handle both array response and object with budgets property
    return Array.isArray(response) ? response : response.budgets || [];
  },

  /**
   * Get a single budget by ID
   */
  get: async (budgetId: string, token: string): Promise<Budget> => {
    return apiClient.get<Budget>(`/budgets/${budgetId}`, token);
  },

  /**
   * Create a new budget
   */
  create: async (data: CreateBudgetRequest, token: string): Promise<Budget> => {
    return apiClient.post<Budget>('/budgets', data, token);
  },

  /**
   * Update an existing budget
   */
  update: async (
    budgetId: string,
    data: UpdateBudgetRequest,
    token: string
  ): Promise<Budget> => {
    return apiClient.put<Budget>(`/budgets/${budgetId}`, data, token);
  },

  /**
   * Delete a budget
   */
  delete: async (budgetId: string, token: string): Promise<void> => {
    return apiClient.delete(`/budgets/${budgetId}`, token);
  },
};
