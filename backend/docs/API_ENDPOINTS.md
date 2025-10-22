# API Endpoints Reference

## Base URLs
- Local: `http://localhost:8000/v1`
- Production: `https://api.moniagent.com/v1`

All routes under `/v1` require `Authorization: Bearer <token>` unless noted. In development, the token `mock-token-for-development` resolves to a stub user.

## Error Format
```json
{
  "detail": "Human readable message",
  "error_code": "OPTIONAL_CODE"
}
```

## Authentication

### Register
```http
POST /auth/register
Content-Type: application/json
```
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!",
  "first_name": "Jamie",
  "last_name": "Lee"
}
```
**Response 200**
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "first_name": "Jamie",
  "last_name": "Lee",
  "created_at": "2025-10-16T08:30:00Z"
}
```

### Login
```http
POST /auth/login
Content-Type: application/x-www-form-urlencoded

username=user@example.com&password=SecurePass123!
```
**Response 200**
```json
{
  "access_token": "jwt-token",
  "token_type": "bearer"
}
```

## Invoice Routes

### Process Invoice (OCR)
```http
POST /invoices/process
Authorization: Bearer <token>
Content-Type: multipart/form-data
```
Form field `file` must be a JPEG or PNG.  
**Response 200**
```json
{
  "invoice_id": "inv-123",
  "store_name": "Whole Foods Market",
  "date": "2025-10-15",
  "total_amount": 45.99,
  "status": "processed"
}
```
Errors: 400 invalid file, 500 OCR failure.

### List Invoices
```http
GET /invoices
Authorization: Bearer <token>
```
**Response 200**
```json
{
  "invoices": [
    {
      "invoice_id": "inv-123",
      "store_name": "Whole Foods Market",
      "date": "2025-10-15",
      "total_amount": 45.99,
      "status": "processed"
    }
  ]
}
```

### Get Invoice
```http
GET /invoices/{invoice_id}
Authorization: Bearer <token>
```
**Response 200** - same schema as above. Returns 403 if the invoice belongs to another user.

## Expense Routes

### Create Expense
```http
POST /expenses
Authorization: Bearer <token>
Content-Type: application/json
```
```json
{
  "merchant_name": "Starbucks",
  "amount": 8.75,
  "date": "2025-10-16",
  "category_id": "cat-coffee",
  "description": "Morning latte"
}
```
**Response 200**
```json
{
  "id": "exp-123",
  "user_id": "user-456",
  "merchant_name": "Starbucks",
  "amount": 8.75,
  "date": "2025-10-16",
  "category_id": "cat-coffee",
  "description": "Morning latte",
  "confirmed_by_user": true,
  "source_type": "manual",
  "created_at": "2025-10-16T08:42:00Z",
  "updated_at": "2025-10-16T08:42:00Z"
}
```
Validation errors return 422; other failures return 400.

### List Expenses
```http
GET /expenses?category_id=<optional>
Authorization: Bearer <token>
```
**Response 200**
```json
{
  "expenses": [
    {
      "id": "exp-123",
      "user_id": "user-456",
      "merchant_name": "Starbucks",
      "amount": 8.75,
      "date": "2025-10-16",
      "category_id": "cat-coffee",
      "description": "Morning latte",
      "confirmed_by_user": true,
      "source_type": "manual",
      "created_at": "2025-10-16T08:42:00Z",
      "updated_at": "2025-10-16T08:42:00Z"
    }
  ]
}
```

### Get Expense
```http
GET /expenses/{expense_id}
Authorization: Bearer <token>
```
Returns the same schema as `ExpenseResponse`. 404 when not found, 403 if the record belongs to a different user.

### Update Expense / Apply Corrections
```http
PUT /expenses/{expense_id}
Authorization: Bearer <token>
Content-Type: application/json
```
```json
{
  "merchant_name": "Blue Bottle Coffee",
  "amount": 9.25,
  "date": "2025-10-17",
  "category_id": "cat-coffee"
}
```
**Response 200**
```json
{
  "id": "exp-123",
  "merchant_name": "Blue Bottle Coffee",
  "amount": 9.25,
  "date": "2025-10-17",
  "category_id": "cat-coffee",
  "confirmed_by_user": true,
  "message": "Expense updated successfully",
  "budget_warning": {
    "category_id": "cat-coffee",
    "category_name": "Coffee",
    "limit": 120.0,
    "spent": 90.0,
    "total_with_new_expense": 99.25,
    "remaining": 20.75,
    "percentage_used": 0.83,
    "alert_threshold": 0.8,
    "warning": true,
    "alert_level": "medium",
    "message": "You are approaching your budget limit for Coffee."
  }
}
```
Missing fields in the request are ignored; an empty payload raises `400`.

### Delete Expense
```http
DELETE /expenses/{expense_id}
Authorization: Bearer <token>
```
**Response 200**
```json
{
  "message": "Expense deleted successfully",
  "expense_id": "exp-123"
}
```

## Category & Rule Routes

### List Categories
```http
GET /categories
Authorization: Bearer <token>
```
**Response 200**
```json
{
  "categories": [
    {
      "id": "cat-coffee",
      "user_id": "user-456",
      "name": "Coffee",
      "description": "Cafe spending",
      "icon": "coffee",
      "color": "#6f4e37",
      "is_system_category": false,
      "display_order": 1,
      "created_at": "2025-10-01T12:00:00Z",
      "updated_at": "2025-10-10T09:30:00Z"
    }
  ]
}
```

### Create Category
```http
POST /categories
Authorization: Bearer <token>
Content-Type: application/json
```
```json
{
  "name": "Subscriptions",
  "description": "Recurring services",
  "icon": "card",
  "color": "#4098d7",
  "display_order": 4
}
```
**Response 200** - returns the full `CategoryResponse`.

### Get / Update / Delete
- `GET /categories/{category_id}` → `CategoryResponse`
- `PUT /categories/{category_id}` (partial update) → `CategoryResponse`
- `DELETE /categories/{category_id}` → `{"message": "Category deleted"}` (400/404 for failures)

### Manage Categorisation Rules
- `POST /categories/rules`  
  ```json
  {
    "category_id": "cat-coffee",
    "store_name_pattern": "Starbucks",
    "rule_type": "keyword",
    "confidence_threshold": 0.8
  }
  ```
  Returns `CategorizationRuleResponse`.
- `GET /categories/rules/{category_id}` → `{"rules": [...]}`  
  Currently returns an empty list unless custom rules exist.

### Suggestions and Confirmations
- `POST /categories/suggest`  
  ```json
  { "expense_id": "exp-123" }
  ```  
  Returns `CategorizationSuggestionResponse` with `suggested_category_id`, `suggested_category_name`, and `confidence_score`.  
- `POST /categories/confirm`  
  ```json
  {
    "expense_id": "exp-123",
    "category_id": "cat-coffee"
  }
  ```  
  Returns `CategorizeExpenseResponse`. `category_id` is mandatory.

## Budgets & Spending

### Create Budget
```http
POST /budgets
Authorization: Bearer <token>
Content-Type: application/json
```
```json
{
  "category_id": "cat-groceries",
  "limit_amount": 400,
  "period": "monthly",
  "alert_threshold": 0.8
}
```
**Response 201**
```json
{
  "id": "budget-123",
  "user_id": "user-456",
  "category_id": "cat-groceries",
  "category_name": "Unknown",
  "limit_amount": 400.0,
  "period": "monthly",
  "spent_amount": 0.0,
  "remaining_amount": 400.0,
  "alert_threshold": 0.8,
  "created_at": "2025-10-16T09:00:00Z",
  "updated_at": "2025-10-16T09:00:00Z"
}
```

### List Budgets
```http
GET /budgets
Authorization: Bearer <token>
```
Returns a JSON array of budget dictionaries. The current implementation returns an empty list until persistence is finalised.

### Get Budget (placeholder)
```http
GET /budgets/{budget_id}
Authorization: Bearer <token>
```
Returns a mock `BudgetResponse` payload. Use only for UI scaffolding until the backing query is implemented.

### Update Budget
```http
PUT /budgets/{budget_id}
Authorization: Bearer <token>
Content-Type: application/json
```
Partial updates supported (`limit_amount`, `alert_threshold`, `period`). Response mirrors `BudgetResponse`.

### Delete Budget
```http
DELETE /budgets/{budget_id}
Authorization: Bearer <token>
```
Responds with HTTP 204 (no body) on success.

### Budget Alerts
```http
GET /budgets/alerts
Authorization: Bearer <token>
```
Returns an array of alert dictionaries. Currently emits an empty array until alert generation is implemented.

### Budget Status Check
```http
GET /budgets/check/{category_id}?amount=<optional>
Authorization: Bearer <token>
```
When a budget exists, the response resembles:
```json
{
  "category_id": "cat-groceries",
  "category_name": "Groceries",
  "limit": 400.0,
  "spent": 320.0,
  "total_with_new_expense": 350.0,
  "remaining": 50.0,
  "percentage_used": 0.875,
  "alert_threshold": 0.8,
  "warning": true,
  "alert_level": "medium",
  "message": "You are approaching your budget limit for Groceries."
}
```
If no budget exists, it returns:
```json
{
  "category_id": "cat-groceries",
  "has_budget": false,
  "message": "No budget set for this category"
}
```

### Spending Summary
```http
GET /spending/summary?period=daily|weekly|monthly
Authorization: Bearer <token>
```
**Response 200**
```json
{
  "period": "monthly",
  "total_spending": 1500.0,
  "by_category": [
    {
      "category_id": "cat-1",
      "category_name": "Eating Out",
      "amount": 500.0,
      "percentage": 33.3
    }
  ],
  "by_week": [
    {
      "week": "2025-W42",
      "amount": 300.0,
      "percentage": 20.0
    }
  ]
}
```
When no database session is provided, canned demo values are returned.

## AI Advice & Chat

### Financial Advice
```http
GET /financial-advice?period=daily|weekly|monthly
Authorization: Bearer <token>
```
**Response 200**
```json
{
  "advice": "You are spending 33% on dining out. Consider cooking at home more often.",
  "recommendations": [
    "Set a weekly dining budget of $75",
    "Prepare meals in advance to reduce impulse purchases"
  ],
  "spending_pattern": "high",
  "period": "monthly",
  "top_spending_category": "Eating Out",
  "top_spending_amount": 500.0
}
```
If the Gemini client is unavailable, a deterministic fallback advice string is returned.

### Start Chat Session
```http
POST /chat/start
Authorization: Bearer <token>
Content-Type: application/json
```
```json
{
  "session_title": "October catch-up"
}
```
**Response 200**
```json
{
  "session_id": "sess-123",
  "message": "Chat session started successfully",
  "initial_message": "Hello! I'm your AI assistant for expense tracking..."
}
```

### Send Message
```http
POST /chat/{session_id}/message
Authorization: Bearer <token>
Content-Type: application/json
```
```json
{
  "content": "I spent $45 at Trader Joe's yesterday",
  "message_type": "text"
}
```
**Response 200**
```json
{
  "message_id": "msg-789",
  "response": "I found an expense for $45.00 at Trader Joe's on 2025-10-15. Does that look right?",
  "extracted_expense": {
    "merchant_name": "Trader Joe's",
    "amount": 45.0,
    "date": "2025-10-15",
    "confidence": 0.85,
    "description": "I spent $45 at Trader Joe's yesterday",
    "suggested_category_id": "cat-groceries",
    "categorization_confidence": 0.67
  },
  "requires_confirmation": true,
  "budget_warning": null,
  "advice": null
}
```

### Confirm Expense (placeholder)
```http
POST /chat/{session_id}/confirm-expense
Authorization: Bearer <token>
Content-Type: application/json
```
Payload mirrors `ExpenseConfirmationRequest` (`confirmed`, optional `corrections`).  
**Response 200** currently returns
```json
{
  "status": "confirmed",
  "message": "Expense confirmed and saved",
  "expense_id": "exp-123"
}
```
This endpoint is a stub and will be replaced with real persistence logic.

### Session History
```http
GET /chat/{session_id}/history
Authorization: Bearer <token>
```
**Response 200**
```json
{
  "session": {
    "id": "sess-123",
    "user_id": "user-456",
    "session_title": "October catch-up",
    "status": "active",
    "created_at": "2025-10-16T08:00:00Z",
    "updated_at": "2025-10-16T08:05:00Z"
  },
  "messages": [
    {
      "id": "msg-1",
      "session_id": "sess-123",
      "role": "user",
      "content": "I spent $45 at Trader Joe's yesterday",
      "created_at": "2025-10-16T08:01:00Z"
    },
    {
      "id": "msg-2",
      "session_id": "sess-123",
      "role": "assistant",
      "content": "I found an expense for $45.00 at Trader Joe's...",
      "created_at": "2025-10-16T08:01:02Z"
    }
  ]
}
```

### Close Session
```http
POST /chat/{session_id}/close
Authorization: Bearer <token>
```
**Response 200**
```json
{
  "status": "closed",
  "session_id": "sess-123",
  "message": "Chat session closed"
}
```

## Rate Limiting & Webhooks
- Rate limiting is not yet enforced but headers may be introduced later (`X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`).
- Webhook support (`invoice.processed`, `expense.categorized`, etc.) is planned; no endpoints exist today.
