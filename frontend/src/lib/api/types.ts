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
  is_confirmation_response?: boolean;  // NEW: Whether this is a response to confirmation prompt
  saved_expense?: SavedExpense | null;  // NEW: Client-side tracking of saved expense
}

export interface ExtractedExpense {
  merchant_name: string | null;
  amount: number | null;
  date: string | null;
  confidence: number | null;
  description: string | null;
}

export interface SavedExpense {
  id: string;
  merchant_name: string;
  amount: number;
  date: string;
  category_id: string;
  category_name?: string;  // NEW: Display name for category
}

export interface SendMessageResponse {
  message_id: string;
  response: string;
  extracted_expense?: ExtractedExpense;
  requires_confirmation?: boolean;
  asking_confirmation?: boolean;
  saved_expense?: SavedExpense;
  budget_warning?: string;
  advice?: string;
  interrupted?: boolean;  // NEW: Whether graph execution was interrupted (waiting for user response)
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

// Category Types
export interface Category {
  id: string;
  user_id: string;
  name: string;
  description?: string;
  icon?: string;
  color?: string;
  is_system_category: boolean;
  display_order: number;
  created_at?: string;
  updated_at?: string;
}

export interface CategoryListResponse {
  categories: Category[];
}

// Budget Types
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

export interface CreateBudgetRequest {
  category_id: string;
  limit_amount: number;
  period: 'monthly' | 'weekly' | 'yearly';
  alert_threshold?: number;
}

export interface UpdateBudgetRequest {
  limit_amount?: number;
  period?: 'monthly' | 'weekly' | 'yearly';
  alert_threshold?: number;
}

export interface BudgetListResponse {
  budgets: Budget[];
}

// Expense Types
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

export interface CreateExpenseRequest {
  merchant_name: string;
  amount: number;
  date: string;
  category_id?: string; // Optional - auto-categorizes if omitted
  description?: string;
}

export interface UpdateExpenseRequest {
  merchant_name?: string;
  amount?: number;
  date?: string;
  category_id?: string;
  description?: string;
}

export interface ExpenseListResponse {
  expenses: Expense[];
}

export interface BudgetWarning {
  category_id: string;
  category_name: string;
  limit: number;
  spent: number;
  total_with_new_expense: number;
  remaining: number;
  percentage_used: number;
  alert_threshold: number;
  warning: boolean;
  alert_level: string;
  message: string;
}
