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

### Initialize Vietnamese Categories (Auto-called on Registration)
```http
POST /auth/init-vietnamese-data
Content-Type: application/json
```
**Response 200**
```json
{
  "status": "success",
  "message": "Vietnamese categories and rules initialized",
  "categories_count": 10,
  "rules_created": 60
}
```
This endpoint is automatically invoked when a new user registers, but can also be called manually for existing users to initialize or update their categories. It:
- Copies 10 Vietnamese system categories
- Creates 60-122 keyword-based categorization rules
- Enables LLM-based auto-categorization

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
  "category_id": "cat-001",
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
  "category_id": "cat-001",
  "category_name": "Ăn uống",
  "description": "Morning latte",
  "confirmed_by_user": true,
  "source_type": "manual",
  "categorization_confidence": 0.95,
  "created_at": "2025-10-16T08:42:00Z",
  "updated_at": "2025-10-16T08:42:00Z"
}
```

**Auto-Categorization**: When the category_id is omitted, the system automatically:
- Uses LLM (Gemini 2.5 Flash) to analyze merchant_name and description against all user's categories
- Returns the best matching category with a confidence score (0.0-1.0)
- Falls back to keyword-based rules if LLM categorization fails
- Stores the categorization_confidence in the expense record

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
      "id": "cat-001",
      "user_id": "user-456",
      "name": "Ăn uống",
      "description": "Ăn ngoài, đi chợ, cafe, nước uống",
      "icon": "🍜",
      "color": "#FF6B6B",
      "is_system_category": true,
      "display_order": 1,
      "created_at": "2025-10-01T12:00:00Z",
      "updated_at": "2025-10-10T09:30:00Z"
    },
    {
      "id": "cat-002",
      "user_id": "user-456",
      "name": "Đi lại",
      "description": "Xăng xe, Grab, vé xe, bảo dưỡng",
      "icon": "🚗",
      "color": "#4ECDC4",
      "is_system_category": true,
      "display_order": 2,
      "created_at": "2025-10-01T12:00:00Z",
      "updated_at": "2025-10-10T09:30:00Z"
    }
  ]
}
```

**Vietnamese Categories Available:**
| # | Name | Icon | Color | Description |
|---|------|------|-------|-------------|
| 1 | Ăn uống | 🍜 | #FF6B6B | Ăn ngoài, đi chợ, cafe, nước uống |
| 2 | Đi lại | 🚗 | #4ECDC4 | Xăng xe, Grab, vé xe, bảo dưỡng |
| 3 | Nhà ở | 🏠 | #95E1D3 | Thuê nhà, điện, nước, internet |
| 4 | Mua sắm cá nhân | 👕 | #F38181 | Quần áo, mỹ phẩm, đồ điện tử |
| 5 | Giải trí & du lịch | 🎬 | #AA96DA | Xem phim, du lịch, game |
| 6 | Giáo dục & học tập | 📚 | #FCBAD3 | Học phí, sách vở, khóa học |
| 7 | Sức khỏe & thể thao | 💪 | #A8E6CF | Thuốc, khám bệnh, gym |
| 8 | Gia đình & quà tặng | 🎁 | #FFD3B6 | Quà, lễ tết, hiếu hỉ |
| 9 | Đầu tư & tiết kiệm | 💰 | #FFAAA5 | Mua cổ phiếu, gửi tiết kiệm |
| 10 | Khác | ⚙️ | #E0E0E0 | Chi phí không thuộc nhóm trên |

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
**Response 200 (First Turn - Asking for Confirmation)**
```json
{
  "message_id": "msg-789",
  "response": "Tôi đã lưu các thông tin chi tiêu sau vào hệ thống:\n📌 **Thông tin chi tiêu:**\n   • Cửa hàng: Trader Joe's\n   • Số tiền: 45,000đ\n   • Ngày: 2025-10-15\n   • Danh mục: Ăn uống\n\nBạn có muốn thay đổi thông tin nào không?",
  "extracted_expense": null,
  "requires_confirmation": false,
  "asking_confirmation": true,
  "saved_expense": {
    "id": "exp-123",
    "merchant_name": "Trader Joe's",
    "amount": 45000,
    "date": "2025-10-15",
    "category_id": "cat-001"
  },
  "budget_warning": null,
  "advice": null
}
```

**Response 200 (Second Turn - No Changes)**
User sends: `{"content": "Không, thông tin đó đúng rồi", "message_type": "text"}`
```json
{
  "message_id": "msg-790",
  "response": "Được rồi! Chi tiêu của bạn đã được lưu vào hệ thống. Bạn có thể tiếp tục nhập chi tiêu khác hoặc tôi có thể giúp gì khác không?",
  "extracted_expense": null,
  "requires_confirmation": false,
  "asking_confirmation": false,
  "saved_expense": null,
  "budget_warning": null,
  "advice": null
}
```

**Response 200 (Second Turn - With Corrections)**
User sends: `{"content": "Thay đổi số tiền thành 50000", "message_type": "text"}`
```json
{
  "message_id": "msg-791",
  "response": "✅ Tôi đã cập nhật chi tiêu với các thay đổi sau:\n   • Số tiền: 50,000đ\n\nThông tin đã được lưu lại vào hệ thống.",
  "extracted_expense": null,
  "requires_confirmation": false,
  "asking_confirmation": false,
  "saved_expense": null,
  "budget_warning": null,
  "advice": null
}
```

**Response Schema Details:**
- `asking_confirmation` (bool): `true` when agent is asking for confirmation/corrections; `false` when processing complete
- `saved_expense` (object|null): Populated when `asking_confirmation=true`. Contains:
  - `id`: Expense ID in database
  - `merchant_name`: Merchant/store name
  - `amount`: Amount in original currency
  - `date`: Expense date (YYYY-MM-DD format)
  - `category_id`: Category assigned to the expense
- Multi-turn flow:
  1. User sends expense info → Agent saves and asks confirmation (`asking_confirmation=true`)
  2. User sends response ("No" or corrections) → Agent processes intent and returns final message (`asking_confirmation=false`)

**Auto-Categorization in Chat**: The AI agent automatically:
- Extracts merchant name and description from user input
- Calls LLM to categorize the expense against Vietnamese categories
- Returns both the suggested category and a confidence score
- Presents the categorization to the user for confirmation or correction

**Confirmation Flow (NEW)**: After saving an expense:
- Agent responds with `asking_confirmation=true` and saved expense details
- User can provide corrections like "Thay đổi số tiền" or "Sửa ngày"
- Agent uses `gemini-2.5-flash-lite` to detect update intent and extract corrections
- Corrections are validated and applied through `ExpenseProcessingService.update_expense`
- All corrections are stored as feedback for future learning