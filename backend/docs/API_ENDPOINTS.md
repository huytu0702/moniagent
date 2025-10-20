# API Endpoints Reference

## Base URL
```
http://localhost:8000/v1
https://api.moniagent.com/v1  (production)
```

## Authentication
All endpoints except `/auth/*` require a JWT token in the Authorization header:
```
Authorization: Bearer <access-token>
```

---

## Authentication Endpoints

### Register User
```http
POST /auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securePassword123",
  "first_name": "John",
  "last_name": "Doe"
}
```

**Response** (201 Created):
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "created_at": "2025-01-01T00:00:00Z"
}
```

**Errors**:
- `409 Conflict`: Email already registered
- `422 Unprocessable Entity`: Validation error

### Login
```http
POST /auth/login
Content-Type: application/x-www-form-urlencoded

username=user@example.com&password=securePassword123
```

**Response** (200 OK):
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer"
}
```

**Errors**:
- `401 Unauthorized`: Invalid credentials
- `404 Not Found`: User not found

---

## Invoice Endpoints

### Upload & Process Invoice
```http
POST /invoices/process
Authorization: Bearer <token>
Content-Type: multipart/form-data

file: <image-file>
```

**Supported Formats**: JPG, PNG
**Max Size**: Not specified

**Response** (200 OK):
```json
{
  "invoice_id": "invoice-uuid",
  "store_name": "Whole Foods Market",
  "date": "2025-01-15",
  "total_amount": 45.99,
  "status": "processed"
}
```

**Errors**:
- `400 Bad Request`: Invalid file format
- `401 Unauthorized`: Missing/invalid token
- `413 Payload Too Large`: File exceeds size limit
- `500 Internal Server Error`: OCR processing failed

### Get Invoice Details
```http
GET /invoices/{invoice_id}
Authorization: Bearer <token>
```

**Response** (200 OK):
```json
{
  "invoice_id": "invoice-uuid",
  "store_name": "Whole Foods Market",
  "date": "2025-01-15",
  "total_amount": 45.99,
  "status": "confirmed"
}
```

### List User Invoices
```http
GET /invoices
Authorization: Bearer <token>
```

**Response** (200 OK):
```json
{
  "invoices": [
    {
      "invoice_id": "invoice-uuid",
      "store_name": "Whole Foods Market",
      "date": "2025-01-15",
      "total_amount": 45.99,
      "status": "confirmed"
    }
  ]
}
```

---

## Expense Endpoints

### Create Expense
```http
POST /expenses
Authorization: Bearer <token>
Content-Type: application/json

{
  "amount": 25.50,
  "date": "2025-01-15",
  "category_id": "category-uuid",
  "description": "Lunch at restaurant",
  "invoice_id": "invoice-uuid"  (optional)
}
```

**Response** (201 Created):
```json
{
  "id": "expense-uuid",
  "user_id": "user-uuid",
  "amount": 25.50,
  "date": "2025-01-15",
  "category_id": "category-uuid",
  "category_name": "Eating Out",
  "description": "Lunch at restaurant",
  "status": "confirmed",
  "created_at": "2025-01-15T12:00:00Z"
}
```

### List Expenses
```http
GET /expenses
Authorization: Bearer <token>

Query Parameters:
  ?category_id=uuid
  ?start_date=2025-01-01&end_date=2025-01-31
  ?skip=0&limit=50
```

**Response** (200 OK):
```json
{
  "items": [
    { "id": "...", "amount": 25.50, "..." }
  ],
  "total": 156,
  "skip": 0,
  "limit": 50
}
```

### Update Expense
```http
PUT /expenses/{expense_id}
Authorization: Bearer <token>
Content-Type: application/json

{
  "category_id": "new-category-uuid",
  "description": "Updated description"
}
```

### Delete Expense
```http
DELETE /expenses/{expense_id}
Authorization: Bearer <token>
```

**Response** (204 No Content)

---

## Category Endpoints

### List Categories
```http
GET /categories
Authorization: Bearer <token>
```

**Response** (200 OK):
```json
{
  "items": [
    {
      "id": "uuid",
      "name": "Eating Out",
      "description": "Restaurants, cafes",
      "icon": "🍽️"
    },
    {
      "id": "uuid",
      "name": "Transportation",
      "description": "Gas, public transit",
      "icon": "🚗"
    }
  ]
}
```

### Create Custom Category
```http
POST /categories
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "Subscriptions",
  "description": "Monthly subscriptions",
  "icon": "📅"
}
```

**Response** (201 Created): Category object

---

## Budget Endpoints

### Create Budget
```http
POST /budgets
Authorization: Bearer <token>
Content-Type: application/json

{
  "category_id": "category-uuid",
  "amount": 500.00,
  "period": "monthly",
  "start_date": "2025-01-01"
}
```

**Period Values**: `daily`, `weekly`, `monthly`, `yearly`

**Response** (201 Created):
```json
{
  "id": "budget-uuid",
  "user_id": "user-uuid",
  "category_id": "category-uuid",
  "amount": 500.00,
  "period": "monthly",
  "spent": 245.50,
  "remaining": 254.50,
  "percentage_used": 49.1,
  "start_date": "2025-01-01",
  "end_date": "2025-01-31",
  "created_at": "2025-01-01T00:00:00Z"
}
```

### List Budgets
```http
GET /budgets
Authorization: Bearer <token>
```

**Response** (200 OK):
```json
{
  "items": [
    { "id": "...", "category_id": "...", "..." }
  ],
  "total": 5
}
```

### Update Budget
```http
PUT /budgets/{budget_id}
Authorization: Bearer <token>
Content-Type: application/json

{
  "amount": 600.00
}
```

### Delete Budget
```http
DELETE /budgets/{budget_id}
Authorization: Bearer <token>
```

---

## AI Agent & Chat Endpoints

### Start Chat Session
```http
POST /chat/start
Authorization: Bearer <token>
Content-Type: application/json

{
  "session_title": "Monthly expense tracking"
}
```

**Response** (200 OK):
```json
{
  "session_id": "session-uuid",
  "message": "Chat session started successfully",
  "initial_message": "Hello! I'm your AI assistant for expense tracking. You can upload an invoice image or describe your expense. What would you like to do?"
}
```

### Send Chat Message
```http
POST /chat/{session_id}/message
Authorization: Bearer <token>
Content-Type: application/json

{
  "content": "I spent $25 on coffee at Starbucks today",
  "message_type": "text"  (or "image" for receipt uploads)
}
```

**Response** (200 OK):
```json
{
  "message_id": "msg-uuid",
  "response": "I found an expense: $25.00 at Starbucks. Is this correct?",
  "extracted_expense": {
    "merchant_name": "Starbucks",
    "amount": 25.00,
    "date": "2025-01-16",
    "confidence": 0.95,
    "description": "coffee"
  },
  "requires_confirmation": true,
  "budget_warning": "You've spent $85 of your $100 Eating Out budget this week",
  "advice": "Consider switching to home coffee to save $200-300 per month"
}
```

### Confirm Expense from Chat
```http
POST /chat/{session_id}/confirm-expense
Authorization: Bearer <token>

Query Parameters:
  ?expense_id=expense-uuid
  &category_id=category-uuid  (optional)
  &confirmed=true
```

### Get Chat Session History
```http
GET /chat/{session_id}/history
Authorization: Bearer <token>
```

**Response** (200 OK):
```json
{
  "session": {
    "id": "session-uuid",
    "user_id": "user-uuid",
    "session_title": "Monthly expense tracking",
    "status": "active",
    "created_at": "2025-01-15T10:00:00Z",
    "updated_at": "2025-01-15T10:30:00Z"
  },
  "messages": [
    {
      "id": "msg-uuid",
      "session_id": "session-uuid",
      "role": "user",
      "content": "I spent $25 on coffee at Starbucks",
      "created_at": "2025-01-15T10:15:00Z"
    },
    {
      "id": "msg-uuid",
      "session_id": "session-uuid",
      "role": "assistant",
      "content": "I extracted this expense information...",
      "created_at": "2025-01-15T10:15:05Z"
    }
  ]
}
```

### Close Chat Session
```http
POST /chat/{session_id}/close
Authorization: Bearer <token>
```

**Response** (200 OK):
```json
{
  "status": "closed",
  "session_id": "session-uuid",
  "message": "Chat session closed"
}
```

### Get Financial Advice
```http
GET /financial-advice
Authorization: Bearer <token>

Query Parameters:
  ?period=monthly  (daily, weekly, monthly)
```

**Response** (200 OK):
```json
{
  "summary": "Your spending this month is 15% higher than average",
  "insights": [
    {
      "category": "Eating Out",
      "trend": "increasing",
      "suggestion": "Consider cooking at home to save $50-100/month"
    }
  ],
  "recommendations": [
    "Set a budget for Eating Out at $300/month",
    "Track Transportation costs more closely"
  ],
  "generated_at": "2025-01-15T10:00:00Z"
}
```

---

## Error Responses

All errors follow this format:

```json
{
  "detail": "Error message describing what went wrong",
  "error_code": "OPTIONAL_ERROR_CODE"
}
```

### Common Status Codes
- `200`: Success
- `201`: Created
- `204`: No Content (successful deletion)
- `400`: Bad Request (validation error)
- `401`: Unauthorized (missing/invalid token)
- `403`: Forbidden (permission denied)
- `404`: Not Found
- `409`: Conflict (e.g., duplicate email)
- `413`: Payload Too Large
- `422`: Unprocessable Entity (validation error)
- `500`: Internal Server Error

---

## Rate Limiting

Coming soon - API endpoints will have rate limiting:
- **Standard Users**: 100 requests/minute
- **Premium Users**: 500 requests/minute
- **File Uploads**: 10 uploads/minute

Headers will include:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 87
X-RateLimit-Reset: 1609459200
```

---

## Webhooks

Coming soon - Real-time event notifications:
- `budget.threshold_reached`
- `expense.categorized`
- `invoice.processed`
