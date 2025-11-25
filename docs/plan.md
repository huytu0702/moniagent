# Implementation Plan: Backend API Integration for Dashboard and Budget Settings

## Overview
Integrate the MoniAgent backend API endpoints for expenses, categories, and budgets into the frontend dashboard and budget-settings components. Currently, these components use hardcoded mock data and need to fetch real data from the backend.

## Current State Analysis

### Frontend Architecture
- **Framework**: Next.js 15.1.4 (App Router) with TypeScript
- **Data Fetching**: Custom APIClient wrapper around native Fetch API (no React Query/SWR)
- **State Management**: React hooks (useState, useEffect) + localStorage for auth
- **Auth Pattern**: Token stored in localStorage, passed explicitly to each API call
- **Error Handling**: Centralized in `src/lib/error-handler.ts`

### Existing Integrations
- ✅ Authentication (login/register) - fully integrated
- ✅ Chat interface - fully integrated with backend
- ❌ Dashboard - uses hardcoded `VIETNAMESE_CATEGORIES` with mock spent/budget data
- ❌ Budget Settings - uses hardcoded categories with local state only
- ❌ Recent Transactions - uses hardcoded transaction array

### Backend API Endpoints Available
From `backend/docs/API_ENDPOINTS.md`:
- `GET /categories` - List all categories
- `GET /categories/{category_id}` - Get single category
- `POST /categories` - Create category
- `PUT /categories/{category_id}` - Update category
- `DELETE /categories/{category_id}` - Delete category
- `POST /budgets` - Create budget
- `GET /budgets` - List budgets
- `GET /budgets/{budget_id}` - Get budget
- `PUT /budgets/{budget_id}` - Update budget
- `DELETE /budgets/{budget_id}` - Delete budget
- `GET /budgets/check/{category_id}` - Check budget status
- `GET /budgets/alerts` - Get budget alerts
- `GET /expenses` - List expenses (supports `?category_id=` filter)
- `GET /expenses/{expense_id}` - Get expense
- `POST /expenses` - Create expense (auto-categorizes if category_id omitted)
- `PUT /expenses/{expense_id}` - Update expense
- `DELETE /expenses/{expense_id}` - Delete expense

---

## Implementation Plan

### Phase 1: Foundation - Types and Utilities

#### 1.1 Add TypeScript Type Definitions
**File**: `src/lib/api/types.ts`

Add the following interfaces to match backend schemas:

```typescript
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
```

#### 1.2 Create Utility Functions
**File**: `src/lib/utils.ts`

Add formatting utilities to replace inline formatting:

```typescript
/**
 * Format currency in Vietnamese Dong
 */
export function formatCurrency(amount: number, locale: string = "vi-VN"): string {
  return `${amount.toLocaleString(locale)}đ`;
}

/**
 * Format date string or Date object
 */
export function formatDate(date: string | Date, locale: string = "vi-VN"): string {
  const dateObj = typeof date === 'string' ? new Date(date) : date;
  return dateObj.toLocaleDateString(locale);
}

/**
 * Format time from date
 */
export function formatTime(date: string | Date, locale: string = "vi-VN"): string {
  const dateObj = typeof date === 'string' ? new Date(date) : date;
  return dateObj.toLocaleTimeString(locale, { hour: "2-digit", minute: "2-digit" });
}

/**
 * Format datetime with full details
 */
export function formatDateTime(date: string | Date, locale: string = "vi-VN"): string {
  const dateObj = typeof date === 'string' ? new Date(date) : date;
  return dateObj.toLocaleString(locale);
}

/**
 * Calculate percentage safely
 */
export function calculatePercentage(numerator: number, denominator: number): number {
  if (denominator === 0) return 0;
  return (numerator / denominator) * 100;
}
```

---

### Phase 2: API Client Modules

#### 2.1 Create Category API Client
**File**: `src/lib/api/category.ts`

```typescript
import { apiClient } from './client';
import { Category, CategoryListResponse } from './types';

export const categoryAPI = {
  /**
   * Get all categories for the current user
   */
  list: async (token: string): Promise<CategoryListResponse> => {
    return apiClient.get<CategoryListResponse>('/categories', token);
  },

  /**
   * Get a single category by ID
   */
  get: async (categoryId: string, token: string): Promise<Category> => {
    return apiClient.get<Category>(`/categories/${categoryId}`, token);
  },
};
```

#### 2.2 Create Budget API Client
**File**: `src/lib/api/budget.ts`

```typescript
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
```

#### 2.3 Create Expense API Client
**File**: `src/lib/api/expense.ts`

```typescript
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
    const response = await apiClient.get<ExpenseListResponse>(endpoint, token);
    return response.expenses;
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
```

#### 2.4 Update API Index
**File**: `src/lib/api/index.ts`

```typescript
export * from './auth';
export * from './chat';
export * from './category';
export * from './budget';
export * from './expense';
export * from './types';
export * from './client';
```

---

### Phase 3: Dashboard Integration

#### 3.1 Update ExpenseDashboard Component
**File**: `src/components/expense-dashboard.tsx`

**Changes Required**:
1. Remove hardcoded `VIETNAMESE_CATEGORIES` constant
2. Add state for loading, error, categories, budgets, and expenses
3. Fetch data on component mount
4. Calculate spent amounts from expenses grouped by category
5. Handle loading and error states

**Key Implementation Details**:
```typescript
"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { authStorage } from "@/lib/auth"
import { categoryAPI, budgetAPI, expenseAPI } from "@/lib/api"
import { Category, Budget, Expense } from "@/lib/api/types"
import { getErrorMessage } from "@/lib/error-handler"
import { formatCurrency, calculatePercentage } from "@/lib/utils"

// Create a merged data structure for rendering
interface CategoryWithBudget extends Category {
  spent: number;
  budget: number;
}

export function ExpenseDashboard() {
  const router = useRouter()
  const [token, setToken] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState("")
  const [categories, setCategories] = useState<CategoryWithBudget[]>([])

  useEffect(() => {
    const accessToken = authStorage.getToken()
    if (!accessToken) {
      router.push("/login")
      return
    }
    setToken(accessToken)
    fetchDashboardData(accessToken)
  }, [router])

  const fetchDashboardData = async (token: string) => {
    setIsLoading(true)
    setError("")
    try {
      // Fetch categories, budgets, and expenses in parallel
      const [categoriesRes, budgets, expenses] = await Promise.all([
        categoryAPI.list(token),
        budgetAPI.list(token),
        expenseAPI.list(token),
      ])

      // Calculate spent amount per category from expenses
      const spentByCategory = expenses.reduce((acc, expense) => {
        acc[expense.category_id] = (acc[expense.category_id] || 0) + expense.amount
        return acc
      }, {} as Record<string, number>)

      // Create budget map for quick lookup
      const budgetByCategory = budgets.reduce((acc, budget) => {
        acc[budget.category_id] = budget.limit_amount
        return acc
      }, {} as Record<string, number>)

      // Merge categories with budget and spent data
      // Show categories with 0 budget if they have no budget configured
      const mergedData: CategoryWithBudget[] = categoriesRes.categories.map(cat => ({
        ...cat,
        spent: spentByCategory[cat.id] || 0,
        budget: budgetByCategory[cat.id] || 0, // 0 if no budget set
      }))

      setCategories(mergedData)
      setExpenses(expenses) // Store expenses for recent transactions
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setIsLoading(false)
    }
  }

  // Calculate totals
  const totalSpent = categories.reduce((sum, cat) => sum + cat.spent, 0)
  const totalBudget = categories.reduce((sum, cat) => sum + cat.budget, 0)
  const percentageUsed = calculatePercentage(totalSpent, totalBudget)

  // Render loading state
  if (isLoading) {
    return <div className="flex min-h-screen items-center justify-center">
      <p className="text-muted-foreground">Đang tải dữ liệu...</p>
    </div>
  }

  // Render error state
  if (error) {
    return <div className="flex min-h-screen items-center justify-center">
      <div className="text-center">
        <p className="text-destructive mb-4">{error}</p>
        <Button onClick={() => token && fetchDashboardData(token)}>Thử lại</Button>
      </div>
    </div>
  }

  // Existing JSX with formatCurrency helper
  // Replace: {totalSpent.toLocaleString("vi-VN")}đ
  // With: {formatCurrency(totalSpent)}
}
```

#### 3.2 Update RecentTransactions Component
**File**: `src/components/recent-transaction.tsx`

**Changes Required**:
1. Accept expenses as props instead of using hardcoded data
2. Fetch category names from categories list
3. Limit to most recent 5 transactions
4. Handle empty state

```typescript
import { Expense, Category } from "@/lib/api/types"
import { formatCurrency, formatDate } from "@/lib/utils"

interface RecentTransactionsProps {
  expenses: Expense[]
  categories: Category[]
}

export function RecentTransactions({ expenses, categories }: RecentTransactionsProps) {
  // Create category lookup map
  const categoryMap = categories.reduce((acc, cat) => {
    acc[cat.id] = cat
    return acc
  }, {} as Record<string, Category>)

  // Get 5 most recent expenses sorted by date
  const recentExpenses = [...expenses]
    .sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime())
    .slice(0, 5)

  if (recentExpenses.length === 0) {
    return (
      <Card className="p-6">
        <h2 className="mb-4 text-xl font-semibold text-foreground">Giao dịch gần đây</h2>
        <p className="text-muted-foreground text-center py-8">Chưa có giao dịch nào</p>
      </Card>
    )
  }

  return (
    <Card className="p-6">
      <h2 className="mb-4 text-xl font-semibold text-foreground">Giao dịch gần đây</h2>
      <div className="space-y-4">
        {recentExpenses.map((expense) => {
          const category = categoryMap[expense.category_id]
          return (
            <div key={expense.id} className="...">
              <div className="flex items-center gap-4">
                <div className="...">{category?.icon || "📝"}</div>
                <div>
                  <p className="...">{expense.merchant_name}</p>
                  <p className="...">{category?.name || "Khác"}</p>
                </div>
              </div>
              <div className="text-right">
                <p className="...">-{formatCurrency(expense.amount)}</p>
                <p className="...">{formatDate(expense.date)}</p>
              </div>
            </div>
          )
        })}
      </div>
    </Card>
  )
}
```

**Update expense-dashboard.tsx to pass props**:
```typescript
<RecentTransactions expenses={expenses} categories={categoriesRes.categories} />
```

---

### Phase 4: Budget Settings Integration

#### 4.1 Update BudgetSettings Component
**File**: `src/components/budget-settings.tsx`

**Changes Required**:
1. Remove hardcoded `VIETNAMESE_CATEGORIES` constant
2. Fetch categories and existing budgets from API
3. Implement save functionality to create/update budgets
4. Add loading and error states
5. Handle budget creation for categories without budgets

**Key Implementation Details**:
```typescript
"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { authStorage } from "@/lib/auth"
import { categoryAPI, budgetAPI } from "@/lib/api"
import { Category, Budget } from "@/lib/api/types"
import { getErrorMessage } from "@/lib/error-handler"
import { formatCurrency } from "@/lib/utils"

export function BudgetSettings() {
  const router = useRouter()
  const [token, setToken] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [error, setError] = useState("")
  const [categories, setCategories] = useState<Category[]>([])
  const [budgets, setBudgets] = useState<Record<string, number>>({})
  const [existingBudgets, setExistingBudgets] = useState<Record<string, Budget>>({})

  useEffect(() => {
    const accessToken = authStorage.getToken()
    if (!accessToken) {
      router.push("/login")
      return
    }
    setToken(accessToken)
    fetchBudgetData(accessToken)
  }, [router])

  const fetchBudgetData = async (token: string) => {
    setIsLoading(true)
    setError("")
    try {
      const [categoriesRes, budgetsList] = await Promise.all([
        categoryAPI.list(token),
        budgetAPI.list(token),
      ])

      setCategories(categoriesRes.categories)

      // Create budget maps
      const budgetAmounts: Record<string, number> = {}
      const existingBudgetMap: Record<string, Budget> = {}

      budgetsList.forEach(budget => {
        budgetAmounts[budget.category_id] = budget.limit_amount
        existingBudgetMap[budget.category_id] = budget
      })

      // Set default 0 for categories without budgets
      categoriesRes.categories.forEach(cat => {
        if (!budgetAmounts[cat.id]) {
          budgetAmounts[cat.id] = 0
        }
      })

      setBudgets(budgetAmounts)
      setExistingBudgets(existingBudgetMap)
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setIsLoading(false)
    }
  }

  const handleBudgetChange = (categoryId: string, value: string) => {
    const numValue = Number.parseInt(value.replace(/\D/g, "")) || 0
    setBudgets(prev => ({ ...prev, [categoryId]: numValue }))
  }

  const handleSave = async () => {
    if (!token) return

    setIsSaving(true)
    setError("")

    try {
      // Create or update budgets for each category
      const promises = categories.map(async (category) => {
        const budgetAmount = budgets[category.id]
        const existingBudget = existingBudgets[category.id]

        if (existingBudget) {
          // Update existing budget if amount changed
          if (existingBudget.limit_amount !== budgetAmount) {
            return budgetAPI.update(
              existingBudget.id,
              { limit_amount: budgetAmount },
              token
            )
          }
        } else if (budgetAmount > 0) {
          // Create new budget only if amount is greater than 0
          return budgetAPI.create(
            {
              category_id: category.id,
              limit_amount: budgetAmount,
              period: 'monthly',
              alert_threshold: 0.8,
            },
            token
          )
        }
      })

      await Promise.all(promises)

      // Refresh data after save
      await fetchBudgetData(token)

      alert("Đã lưu cài đặt ngân sách!")
    } catch (err) {
      setError(getErrorMessage(err))
      alert("Có lỗi xảy ra khi lưu ngân sách: " + getErrorMessage(err))
    } finally {
      setIsSaving(false)
    }
  }

  const totalBudget = Object.values(budgets).reduce((sum, budget) => sum + budget, 0)

  // Loading state
  if (isLoading) {
    return <div className="flex min-h-screen items-center justify-center">
      <p className="text-muted-foreground">Đang tải dữ liệu...</p>
    </div>
  }

  // Existing JSX structure with:
  // - formatCurrency for display
  // - disabled={isSaving} on Save button
  // - Error display if error exists
}
```

---

### Phase 5: Component Props Updates

#### 5.1 Update CategoryCard Component
**File**: `src/components/category-card.tsx`

No changes needed - component already accepts the correct shape via props.

#### 5.2 Update ExpenseChart Component
**File**: `src/components/expense-chart.tsx`

No changes needed - component already accepts the correct shape via props.

---

### Phase 6: Error Handling & Edge Cases

#### 6.1 Handle Empty States
- Dashboard with no categories: Show onboarding message
- Dashboard with no expenses: Show "Chưa có chi tiêu nào" message
- Budget settings with no categories: Show initialization prompt

#### 6.2 Handle Network Errors
- Use existing error handler from `src/lib/error-handler.ts`
- Display user-friendly error messages
- Provide "Retry" buttons for failed requests

#### 6.3 Handle Token Expiry
- Redirect to login on 401 responses
- Clear token from localStorage
- Show appropriate message to user

---

## Testing Checklist

### Dashboard
- [ ] Loads categories from backend
- [ ] Loads budgets from backend
- [ ] Loads expenses from backend
- [ ] Calculates spent amounts correctly
- [ ] Shows loading state during fetch
- [ ] Handles errors gracefully
- [ ] Displays correct totals
- [ ] Shows budget warnings for categories over 80%
- [ ] Recent transactions show latest 5 expenses
- [ ] Recent transactions display correct category icons
- [ ] Redirects to login if not authenticated

### Budget Settings
- [ ] Loads categories from backend
- [ ] Loads existing budgets
- [ ] Shows 0 for categories without budgets
- [ ] Updates existing budgets on save
- [ ] Creates new budgets on save
- [ ] Calculates total budget correctly
- [ ] Shows loading state during operations
- [ ] Handles errors gracefully
- [ ] Shows success message after save
- [ ] Refreshes data after save
- [ ] Redirects to login if not authenticated

### API Integration
- [ ] Category API client works correctly
- [ ] Budget API client works correctly
- [ ] Expense API client works correctly
- [ ] Token is passed to all requests
- [ ] 401 errors trigger logout
- [ ] Network errors show user-friendly messages
- [ ] Multiple parallel requests work correctly

---

## Critical Files to Modify

1. **New Files**:
   - `src/lib/api/category.ts` - Category API client
   - `src/lib/api/budget.ts` - Budget API client
   - `src/lib/api/expense.ts` - Expense API client

2. **Files to Update**:
   - `src/lib/api/types.ts` - Add Category, Budget, Expense types
   - `src/lib/api/index.ts` - Export new API clients
   - `src/lib/utils.ts` - Add formatting utilities
   - `src/components/expense-dashboard.tsx` - Integrate API calls
   - `src/components/budget-settings.tsx` - Integrate API calls
   - `src/components/recent-transaction.tsx` - Accept props instead of hardcoded data

---

## Implementation Order

1. **Phase 1** (Foundation): Types and utilities - establishes data contracts
2. **Phase 2** (API Clients): Create API client modules - enables data fetching
3. **Phase 3** (Dashboard): Integrate dashboard with backend - shows real data
4. **Phase 4** (Budget Settings): Integrate budget settings - enables budget management
5. **Phase 5** (Polish): Update child components, handle edge cases
6. **Phase 6** (Testing): Verify all functionality works end-to-end

---

## Notes & Considerations

- **Vietnamese Categories**: The backend initializes 10 system categories on user registration. The frontend should fetch these dynamically rather than hardcode them.
- **Budget Period**: All budgets will use "monthly" period initially. Can be extended later.
- **Alert Threshold**: Default to 0.8 (80%) for budget warnings.
- **Auto-Categorization**: When creating expenses via dashboard (future feature), omit category_id to let backend LLM categorize automatically.
- **State Management**: ✅ Use plain React hooks (useState/useEffect) - consistent with existing codebase.
- **Data Source**: ✅ Fetch expenses separately and calculate spent amounts client-side - provides flexibility and enables recent transactions display.
- **Categories Without Budgets**: ✅ Show categories with 0 budget - allows users to see all spending even without budget limits.
- **Caching**: Currently no caching. All requests use `cache: 'no-store'`. Consider adding cache strategy later.
- **Optimistic Updates**: Not implemented. All updates wait for server response. Can be added for better UX.
- **Real-time Updates**: Not implemented. Consider WebSocket or polling for multi-device sync in future.

---

## Success Criteria

✅ Dashboard displays real data from backend API
✅ Budget settings can create and update budgets
✅ Recent transactions show actual expense data
✅ Loading states provide feedback during data fetching
✅ Error handling provides clear user feedback
✅ Authentication is properly enforced
✅ All components use new formatting utilities
✅ Type safety maintained throughout
