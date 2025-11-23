export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  first_name: string;
  last_name: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  expires_in?: number; // Optional, will be set to default if not provided
}

export interface User {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  created_at: string;
}

export interface UserRegisterResponse {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  created_at: string;
}

export interface StartChatRequest {
  session_title: string;
}

export interface StartChatResponse {
  session_id: string;
  message: string;
  initial_message: string;
}

export interface SendMessageRequest {
  content: string;
  message_type: 'text' | 'image';
}

export interface ExtractedExpense {
  merchant_name: string;
  amount: number;
  date: string;
  confidence: number;
  description: string;
}

export interface SendMessageResponse {
  message_id: string;
  response: string;
  extracted_expense?: ExtractedExpense;
  requires_confirmation?: boolean;
  budget_warning?: string;
  advice?: string;
}

export interface ChatMessage {
  id: string;
  session_id: string;
  role: 'user' | 'assistant';
  content: string;
  created_at: string;
}

export interface ChatSession {
  id: string;
  user_id: string;
  session_title: string;
  status: 'active' | 'closed';
  created_at: string;
  updated_at: string;
}

export interface ChatHistoryResponse {
  session: ChatSession;
  messages: ChatMessage[];
}

export interface Expense {
  id: string;
  user_id: string;
  merchant_name: string;
  amount: number;
  date: string;
  category_id: string;
  category_name?: string;
  description?: string;
  confirmed_by_user: boolean;
  source_type: string;
  categorization_confidence?: number;
  created_at: string;
  updated_at: string;
}

export interface Budget {
  id: string;
  user_id: string;
  category_id: string;
  category_name: string;
  limit_amount: number;
  period: string;
  spent_amount: number;
  remaining_amount: number;
  alert_threshold: number;
  created_at: string;
  updated_at: string;
}

export interface Category {
  id: string;
  user_id: string;
  name: string;
  description: string;
  icon: string;
  color: string;
  is_system_category: boolean;
  display_order: number;
  created_at: string;
  updated_at: string;
}

export interface DashboardStats {
  totalExpenses: number;
  monthlySpending: number;
  budgetUtilization: number;
  topCategory: string;
}