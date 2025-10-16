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
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securePassword123"
}
```

**Response** (200 OK):
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

**Errors**:
- `401 Unauthorized`: Invalid credentials
- `404 Not Found`: User not found

---

## Invoice Endpoints

### Upload & Process Invoice
```http
POST /invoices
Authorization: Bearer <token>
Content-Type: multipart/form-data

file: <image-file>
```

**Supported Formats**: JPG, PNG, PDF
**Max Size**: 25MB

**Response** (201 Created):
```json
{
  "id": "invoice-uuid",
  "user_id": "user-uuid",
  "store_name": "Whole Foods Market",
  "invoice_date": "2025-01-15",
  "total_amount": 45.99,
  "status": "pending_review",
  "image_url": "https://...",
  "created_at": "2025-01-15T10:30:00Z"
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
  "id": "invoice-uuid",
  "user_id": "user-uuid",
  "store_name": "Whole Foods Market",
  "invoice_date": "2025-01-15",
  "total_amount": 45.99,
  "status": "confirmed",
  "items": [
    {
      "description": "Organic Bananas",
      "quantity": 2,
      "price": 5.99
    }
  ],
  "created_at": "2025-01-15T10:30:00Z",
  "updated_at": "2025-01-15T11:00:00Z"
}
```

### Update Invoice
```http
PUT /invoices/{invoice_id}
Authorization: Bearer <token>
Content-Type: application/json

{
  "store_name": "Whole Foods Market (Edited)",
  "total_amount": 46.99,
  "status": "confirmed"
}
```

**Response** (200 OK): Updated invoice object

**Errors**:
- `404 Not Found`: Invoice not found
- `403 Forbidden`: User doesn't own this invoice

### List User Invoices
```http
GET /invoices
Authorization: Bearer <token>

Query Parameters:
  ?status=pending_review,confirmed
  ?skip=0&limit=20
  ?start_date=2025-01-01&end_date=2025-01-31
```

**Response** (200 OK):
```json
{
  "items": [
    { "id": "...", "store_name": "...", "..." }
  ],
  "total": 42,
  "skip": 0,
  "limit": 20
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

## AI Agent Endpoints

### Categorize Expense
```http
POST /ai-agent/categorize-expense
Authorization: Bearer <token>
Content-Type: application/json

{
  "store_name": "Whole Foods",
  "amount": 45.99,
  "description": "Grocery shopping"
}
```

**Response** (200 OK):
```json
{
  "suggested_category_id": "category-uuid",
  "category_name": "Groceries",
  "confidence": 0.92,
  "alternative_categories": [
    {
      "category_id": "uuid",
      "category_name": "Shopping",
      "confidence": 0.05
    }
  ]
}
```

### Get Financial Advice
```http
GET /ai-agent/financial-advice
Authorization: Bearer <token>

Query Parameters:
  ?period=monthly
  ?category_id=uuid  (optional)
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
