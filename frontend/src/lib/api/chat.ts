import { apiClient } from './client';
import {
  StartChatRequest,
  StartChatResponse,
  SendMessageRequest,
  SendMessageResponse,
  ChatHistoryResponse,
} from './types';

export const chatAPI = {
  /**
   * Bắt đầu phiên chat mới
   */
  startSession: async (data: StartChatRequest, token: string): Promise<StartChatResponse> => {
    return apiClient.post<StartChatResponse>('/chat/start', data, token);
  },

  /**
   * Gửi tin nhắn trong phiên chat
   */
  sendMessage: async (
    sessionId: string,
    data: SendMessageRequest,
    token: string
  ): Promise<SendMessageResponse> => {
    return apiClient.post<SendMessageResponse>(
      `/chat/${sessionId}/message`,
      data,
      token
    );
  },

  /**
   * Gửi ảnh hóa đơn trong phiên chat
   */
  sendImageMessage: async (
    sessionId: string,
    file: File,
    content?: string,
    isConfirmationResponse?: boolean,
    savedExpense?: any,
    token?: string
  ): Promise<SendMessageResponse> => {
    const formData = new FormData();
    formData.append('file', file);
    if (content) {
      formData.append('content', content);
    }
    if (isConfirmationResponse !== undefined) {
      formData.append('is_confirmation_response', isConfirmationResponse.toString());
    }
    if (savedExpense) {
      formData.append('saved_expense', JSON.stringify(savedExpense));
    }

    return apiClient.postMultipart<SendMessageResponse>(
      `/chat/${sessionId}/message/image`,
      formData,
      token
    );
  },

  /**
   * Xác nhận expense từ chat
   */
  confirmExpense: async (
    sessionId: string,
    expenseId: string,
    confirmed: boolean,
    token: string,
    categoryId?: string
  ): Promise<{ status: string; message: string }> => {
    const params = new URLSearchParams();
    params.append('expense_id', expenseId);
    params.append('confirmed', confirmed.toString());
    if (categoryId) {
      params.append('category_id', categoryId);
    }

    return apiClient.post(
      `/chat/${sessionId}/confirm-expense?${params.toString()}`,
      {},
      token
    );
  },

  /**
   * Lấy lịch sử chat
   */
  getHistory: async (sessionId: string, token: string): Promise<ChatHistoryResponse> => {
    return apiClient.get<ChatHistoryResponse>(
      `/chat/${sessionId}/history`,
      token
    );
  },

  /**
   * Đóng phiên chat
   */
  closeSession: async (
    sessionId: string,
    token: string
  ): Promise<{ status: string; session_id: string; message: string }> => {
    return apiClient.post(`/chat/${sessionId}/close`, {}, token);
  },
};
