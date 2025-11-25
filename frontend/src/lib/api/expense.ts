import { apiClient } from './client';
import {
  Expense,
  ExpenseListResponse,
  CreateExpenseRequest,
  UpdateExpenseRequest
} from './types';

export const expenseAPI = {
  /**
   * Get all expenses for the current user
   * @param categoryId - Optional filter by category
   */
  list: async (token: string, categoryId?: string): Promise<Expense[]> => {
    const endpoint = categoryId
      ? `/expenses?category_id=${categoryId}`
      : '/expenses';
    const response = await apiClient.get<Expense[] | ExpenseListResponse>(endpoint, token);
    // Handle both array response and object with expenses property
    return Array.isArray(response) ? response : (response?.expenses || []);
  },

  /**
   * Get a single expense by ID
   */
  get: async (expenseId: string, token: string): Promise<Expense> => {
    return apiClient.get<Expense>(`/expenses/${expenseId}`, token);
  },

  /**
   * Create a new expense
   */
  create: async (data: CreateExpenseRequest, token: string): Promise<Expense> => {
    return apiClient.post<Expense>('/expenses', data, token);
  },

  /**
   * Update an existing expense
   */
  update: async (
    expenseId: string,
    data: UpdateExpenseRequest,
    token: string
  ): Promise<Expense> => {
    return apiClient.put<Expense>(`/expenses/${expenseId}`, data, token);
  },

  /**
   * Delete an expense
   */
  delete: async (expenseId: string, token: string): Promise<{ message: string; expense_id: string }> => {
    return apiClient.delete(`/expenses/${expenseId}`, token);
  },
};
