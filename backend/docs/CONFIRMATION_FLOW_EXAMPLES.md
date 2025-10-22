# AI Agent Confirmation Flow - Detailed Examples

## Overview
This document provides step-by-step examples of how the AI agent works, including the new confirmation flow feature. All examples use Vietnamese language as per the system's localization.

---

## Example 1: Complete Happy Path (Extract → Confirm → Save)

### Step 1: User Registers and Starts Chat Session

**Request:**
```http
POST /v1/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePass123!",
  "first_name": "Nguyễn",
  "last_name": "Văn A"
}
```

**Response (200 OK):**
```json
{
  "id": "user-550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "first_name": "Nguyễn",
  "last_name": "Văn A",
  "created_at": "2025-10-22T10:00:00Z"
}
```

**Vietnamese Categories Automatically Initialized:**
- ✅ 10 system categories created (Ăn uống, Đi lại, Nhà ở, etc.)
- ✅ 60+ keyword-based categorization rules
- ✅ LLM categorization enabled

---

### Step 2: User Starts Chat Session

**Request:**
```http
POST /v1/chat/start
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "session_title": "Chi tiêu ngày 22/10"
}
```

**Response (200 OK):**
```json
{
  "session_id": "session-550e8400-e29b-41d4-a716-446655440001",
  "message": "Chat session started successfully",
  "initial_message": "Xin chào! Tôi là trợ lý AI của bạn để quản lý chi tiêu. Bạn có thể:\n1. Tải ảnh hoá đơn để tôi trích xuất thông tin\n2. Nhập chi tiêu của bạn (ví dụ: 'Tôi vừa mua cà phê 25,000đ')\n\nBạn muốn làm gì?"
}
```

---

### Step 3: User Sends First Expense Message

**Request:**
```http
POST /v1/chat/session-550e8400-e29b-41d4-a716-446655440001/message
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "content": "Tôi vừa mua cà phê 25000 đồng tại Starbucks hôm nay",
  "message_type": "text"
}
```

**Behind the Scenes - LangGraph Agent Processing:**
```
1. extract_expense node:
   - Parses: merchant="Starbucks", amount=25000, description="cà phê"
   - Date extracted as today (2025-10-22)
   - Status: Valid expense extracted ✓

2. process_confirmation node:
   - Calls ExpenseProcessingService.save_expense()
   - Expense saved to DB with ID: exp-550e8400-e29b-41d4-a716-446655440010
   - Calls categorize_expense_with_llm() with merchant name + description
   - LLM response: category_id=cat-001 (Ăn uống), confidence=0.95
   - Checks budget status - No warning for today

3. ask_confirmation node:
   - Formats saved expense details
   - Creates confirmation message
   - Sets asking_confirmation=true

4. llm_call node:
   - Returns formatted response to client
```

**Response (200 OK) - Agent Asking for Confirmation:**
```json
{
  "message_id": "msg-550e8400-e29b-41d4-a716-446655440020",
  "response": "Tôi đã lưu các thông tin chi tiêu sau vào hệ thống:\n\n📌 **Thông tin chi tiêu:**\n   • Cửa hàng: Starbucks\n   • Số tiền: 25,000đ\n   • Ngày: 2025-10-22\n   • Danh mục: Ăn uống 🍜\n\nBạn có muốn thay đổi thông tin nào không? (Nếu có, hãy cho tôi biết chi tiết thay đổi)",
  "extracted_expense": null,
  "requires_confirmation": false,
  "asking_confirmation": true,
  "saved_expense": {
    "id": "exp-550e8400-e29b-41d4-a716-446655440010",
    "merchant_name": "Starbucks",
    "amount": 25000,
    "date": "2025-10-22",
    "category_id": "cat-001"
  },
  "budget_warning": null,
  "advice": null
}
```

**Key Fields Explained:**
- `asking_confirmation: true` → Frontend knows to show confirmation UI
- `saved_expense` → Contains the saved expense details for display
- `extracted_expense: null` → No new extraction happening
- Message has Vietnamese formatting with emoji and clear structure

---

### Step 4a: User Confirms (No Changes)

**Request:**
```http
POST /v1/chat/session-550e8400-e29b-41d4-a716-446655440001/message
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "content": "Không, thông tin đó đúng rồi",
  "message_type": "text"
}
```

**Behind the Scenes - Intent Detection:**
```
1. detect_update_intent node (gemini-2.5-flash-lite):
   - Prompt: "Người dùng có muốn thay đổi thông tin không?"
   - User message: "Không, thông tin đó đúng rồi"
   - LLM Response JSON:
     {
       "wants_update": false,
       "corrections": {}
     }
   - Decision: User does NOT want to update

2. Route to llm_call:
   - Generate confirmation message
   - User message saved to ChatMessage table
```

**Response (200 OK) - Confirmation Complete:**
```json
{
  "message_id": "msg-550e8400-e29b-41d4-a716-446655440021",
  "response": "Được rồi! Chi tiêu của bạn đã được lưu vào hệ thống. Bạn có thể tiếp tục nhập chi tiêu khác hoặc tôi có thể giúp gì khác không?",
  "extracted_expense": null,
  "requires_confirmation": false,
  "asking_confirmation": false,
  "saved_expense": null,
  "budget_warning": null,
  "advice": null
}
```

**Database State After Confirmation:**
- Expense table: `exp-550e8400-e29b-41d4-a716-446655440010` with status=confirmed
- Chat message table: 3 entries (initial + 2 turns)
- No corrections stored (user didn't change anything)

---

## Example 2: With Corrections (Update Intent)

### Step 4b: User Wants to Make Corrections

**Request:**
```http
POST /v1/chat/session-550e8400-e29b-41d4-a716-446655440001/message
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "content": "Chờ, tôi muốn thay đổi số tiền thành 35000 đ, vì tôi mua cà phê latte lớn. Cửa hàng là Blue Bottle chứ không phải Starbucks",
  "message_type": "text"
}
```

**Behind the Scenes - Full Correction Flow:**

```
1. detect_update_intent node (gemini-2.5-flash-lite):
   - Prompt: "Người dùng có muốn thay đổi thông tin không?"
   - User message: "Chờ, tôi muốn thay đổi số tiền thành 35000..."
   - LLM Response JSON:
     {
       "wants_update": true,
       "corrections": {
         "merchant_name": "Blue Bottle",
         "amount": 35000,
         "date": null
       }
     }
   - Decision: User WANTS to update ✓

2. extract_corrections_from_message node (gemini-2.5-flash-lite):
   - Extract detailed corrections from user message
   - Validated fields:
     • merchant_name: "Blue Bottle" ✓
     • amount: 35000 ✓
     • date: null (no change mentioned)

3. process_update node:
   - Call ExpenseProcessingService.update_expense():
     - expense_id: "exp-550e8400-e29b-41d4-a716-446655440010"
     - corrections: {"merchant_name": "Blue Bottle", "amount": 35000}
   - Validation checks:
     • merchant_name: "Blue Bottle" - valid string ✓
     • amount: 35000 - positive number ✓
     • store_learning: true (for future categorization)

4. Database Updates:
   - Update Expense table: merchant_name, amount fields
   - Create CategorizationFeedback record:
     {
       "expense_id": "exp-...",
       "original_category_id": "cat-001",
       "suggested_category_id": "cat-001",
       "user_confirmed_category": "cat-001",
       "merchant_name_correction": "Starbucks → Blue Bottle",
       "created_at": timestamp
     }

5. Budget Re-check:
   - New amount: 35000 (vs original 25000)
   - Check if exceeds budget for "Ăn uống" category
   - Result: No warning (still within budget)

6. Generate Response:
   - Format success message with updated values
   - Include user improvements
```

**Response (200 OK) - Corrections Applied:**
```json
{
  "message_id": "msg-550e8400-e29b-41d4-a716-446655440022",
  "response": "✅ Tôi đã cập nhật chi tiêu với các thay đổi sau:\n   • Cửa hàng: Blue Bottle\n   • Số tiền: 35,000đ\n\nThông tin đã được lưu lại vào hệ thống. Cảm ơn bạn đã giúp tôi học hỏi - tôi sẽ nhớ rằng 'cà phê latte lớn' thường là Blue Bottle!",
  "extracted_expense": null,
  "requires_confirmation": false,
  "asking_confirmation": false,
  "saved_expense": null,
  "budget_warning": null,
  "advice": null
}
```

---

## Example 3: With Budget Warning and Financial Advice

### Scenario: User's spending is approaching budget limit

**Request:**
```http
POST /v1/chat/session-550e8400-e29b-41d4-a716-446655440001/message
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "content": "Tôi vừa mua cơm chiên tôm 150000 đ tại Phở Lâu",
  "message_type": "text"
}
```

**Assumption - User's Budget:**
- Category: "Ăn uống" 
- Monthly limit: 500,000đ
- Already spent this month: 350,000đ
- Remaining: 150,000đ
- Alert threshold: 80%
- This transaction: 150,000đ → Total: 500,000đ (exactly at limit!)

**Behind the Scenes:**

```
1. extract_expense → Valid ✓
2. process_confirmation:
   - Save expense
   - Check budget status
   - New total: 500,000đ / 500,000đ = 100%
   - Alert level: CRITICAL (exceeds 80% threshold)
   - Budget warning generated:
     {
       "category_id": "cat-001",
       "category_name": "Ăn uống",
       "limit": 500000,
       "spent": 500000,
       "percentage_used": 1.0,
       "alert_threshold": 0.8,
       "alert_level": "critical",
       "message": "⚠️ Bạn đã sử dụng hết hạn mức chi tiêu cho danh mục 'Ăn uống' trong tháng này!"
     }

3. ask_confirmation:
   - Still asks for confirmation
   - Sets asking_confirmation=true

4. Response includes budget warning
```

**Response - With Budget Warning:**
```json
{
  "message_id": "msg-550e8400-e29b-41d4-a716-446655440023",
  "response": "Tôi đã lưu các thông tin chi tiêu sau vào hệ thống:\n\n📌 **Thông tin chi tiêu:**\n   • Cửa hàng: Phở Lâu\n   • Số tiền: 150,000đ\n   • Ngày: 2025-10-22\n   • Danh mục: Ăn uống 🍜\n\n⚠️ **CẢNH BÁO NGÂN SÁCH:**\nBạn đã sử dụng hết hạn mức chi tiêu cho danh mục 'Ăn uống' trong tháng này (500,000đ/500,000đ)!\n\nBạn có muốn thay đổi thông tin nào không?",
  "extracted_expense": null,
  "requires_confirmation": false,
  "asking_confirmation": true,
  "saved_expense": {
    "id": "exp-550e8400-e29b-41d4-a716-446655440011",
    "merchant_name": "Phở Lâu",
    "amount": 150000,
    "date": "2025-10-22",
    "category_id": "cat-001"
  },
  "budget_warning": "⚠️ Bạn đã sử dụng hết hạn mức chi tiêu cho danh mục 'Ăn uống' trong tháng này!",
  "advice": null
}
```

### Step 5: User Confirms with Budget Warning

**Request:**
```http
POST /v1/chat/session-550e8400-e29b-41d4-a716-446655440001/message
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "content": "Thì cứ thế, nhưng cho tôi lời khuyên về cách quản lý chi tiêu",
  "message_type": "text"
}
```

**Behind the Scenes:**

```
1. detect_update_intent (gemini-2.5-flash-lite):
   - User message contains "thì cứ thế" (so let it be)
   - LLM Response:
     {
       "wants_update": false,
       "corrections": {}
     }

2. generate_advice node (activated due to budget warning):
   - Call FinancialAdviceService.get_financial_advice()
   - Analysis:
     • Period: monthly
     • Spending pattern: High in "Ăn uống" (100% of budget)
     • Average daily spend: 22,727đ/day
     • Pattern category: HIGH_SPENDER
   - Generate recommendations:
     {
       "advice": "Bạn đang chi tiêu cao cho ăn uống. Cân nhắc giảm chi tiêu ở quán ăn và nấu ăn tại nhà để tiết kiệm được khoảng 100,000-150,000đ/tháng.",
       "recommendations": [
         "Nấu cơm tại nhà thay vì ăn ngoài 3-4 lần/tuần",
         "Sử dụng ứng dụng để theo dõi chi tiêu hàng ngày",
         "Đặt mục tiêu giảm 20% chi tiêu ăn uống tháng sau"
       ]
     }
```

**Response - With Financial Advice:**
```json
{
  "message_id": "msg-550e8400-e29b-41d4-a716-446655440024",
  "response": "Được rồi! Chi tiêu của bạn đã được lưu vào hệ thống.\n\n💡 **GỢI Ý TÀI CHÍNH:**\nBạn đang chi tiêu cao cho ăn uống. Cân nhắc giảm chi tiêu ở quán ăn và nấu ăn tại nhà để tiết kiệm được khoảng 100,000-150,000đ/tháng.\n\n📋 **CÁC KHUYẾN NGHỊ:**\n  • Nấu cơm tại nhà thay vì ăn ngoài 3-4 lần/tuần\n  • Sử dụng ứng dụng để theo dõi chi tiêu hàng ngày\n  • Đặt mục tiêu giảm 20% chi tiêu ăn uống tháng sau\n\nBạn có thêm chi tiêu nào khác cần lưu không?",
  "extracted_expense": null,
  "requires_confirmation": false,
  "asking_confirmation": false,
  "saved_expense": null,
  "budget_warning": "⚠️ Bạn đã sử dụng hết hạn mức chi tiêu cho danh mục 'Ăn uống' trong tháng này!",
  "advice": "Bạn đang chi tiêu cao cho ăn uống. Cân nhắc giảm chi tiêu ở quán ăn và nấu ăn tại nhà để tiết kiệm được khoảng 100,000-150,000đ/tháng."
}
```

---

## Example 4: Invalid Input → Clarification Request

**Request:**
```http
POST /v1/chat/session-550e8400-e29b-41d4-a716-446655440001/message
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "content": "Hôm nay tôi đi chơi",
  "message_type": "text"
}
```

**Behind the Scenes:**
```
1. extract_expense node:
   - Parse: "Hôm nay tôi đi chơi"
   - No merchant name detected ✗
   - No amount detected ✗
   - No date detected (too vague) ✗
   - Result: Invalid expense extraction

2. Route to llm_call:
   - No structured data to save
   - Generate clarification prompt
```

**Response - Asking for Clarification:**
```json
{
  "message_id": "msg-550e8400-e29b-41d4-a716-446655440025",
  "response": "Tôi hiểu bạn đi chơi hôm nay! Nhưng để lưu chi tiêu, tôi cần thêm thông tin:\n\n1️⃣ **Bạn đã chi tiêu bao nhiêu tiền?** (Ví dụ: 100,000đ)\n2️⃣ **Chi tiêu ở đâu?** (Ví dụ: Công viên, quán cà phê, ...)\n3️⃣ **Chi tiêu cho cái gì?** (Ví dụ: Vé vào cửa, đồ ăn, vé xe, ...)\n\nVí dụ: 'Tôi chi 150,000đ cho vé vào Công viên Yên Sở'",
  "extracted_expense": null,
  "requires_confirmation": false,
  "asking_confirmation": false,
  "saved_expense": null,
  "budget_warning": null,
  "advice": null
}
```

---

## Example 5: Image Upload (Invoice OCR)

**Request:**
```http
POST /v1/invoices/process
Authorization: Bearer <jwt_token>
Content-Type: multipart/form-data

file: [image file: restaurant_receipt.jpg]
```

**Behind the Scenes - OCR Processing:**
```
1. InvoiceService.process_invoice_upload():
   - Stream image to OCRService
   - OCRService.process_invoice() → Gemini 2.5 Flash
   - LLM extracts:
     • merchant: "Nhà hàng Tiên Sơn"
     • total_amount: 850000
     • date: 2025-10-22
     • items: ["Cơm tấm chiên", "Nem rán", "Nước cam"]

2. Create Invoice record
```

**Invoice Response:**
```json
{
  "invoice_id": "inv-550e8400-e29b-41d4-a716-446655440030",
  "store_name": "Nhà hàng Tiên Sơn",
  "date": "2025-10-22",
  "total_amount": 850000,
  "status": "processed"
}
```

**Then User Creates Expense from Invoice:**
```http
POST /v1/expenses
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "merchant_name": "Nhà hàng Tiên Sơn",
  "amount": 850000,
  "date": "2025-10-22",
  "description": "Cơm tấm chiên, nem rán, nước cam"
}
```

**Auto-Categorization:**
```
→ LLM categorizes: "Ăn uống" with confidence 0.98
→ Expense saved with category

OR in Chat:
→ User sends: "Tôi vừa ăn tại Nhà hàng Tiên Sơn 850,000đ"
→ Agent extracts and asks for confirmation
→ Same workflow as Examples 1-3
```

---

## Database State Summary

After completing all examples, the database contains:

**Expenses Table:**
```
ID                                    | Merchant         | Amount   | Date       | Category  | Status
exp-550e8400...0010                  | Blue Bottle      | 35000    | 2025-10-22 | Ăn uống   | confirmed
exp-550e8400...0011                  | Phở Lâu          | 150000   | 2025-10-22 | Ăn uống   | confirmed
```

**Chat Sessions Table:**
```
ID                                    | User ID              | Title              | Status
session-550e8400...0001              | user-550e8400...0000 | Chi tiêu ngày 22/10| active
```

**Chat Messages Table:**
```
ID     | Session ID | Role      | Content
msg-20 | session-1  | user      | "Tôi vừa mua cà phê 25000..."
msg-21 | session-1  | assistant | "Tôi đã lưu các thông tin..."
msg-22 | session-1  | user      | "Không, thông tin đó đúng rồi"
msg-23 | session-1  | assistant | "Được rồi! Chi tiêu..."
msg-24 | session-1  | user      | "Chờ, tôi muốn thay đổi..."
msg-25 | session-1  | assistant | "✅ Tôi đã cập nhật..."
... (more messages)
```

**Categorization Feedback Table:**
```
ID  | Expense ID        | Original Category | Correction
1   | exp-550e8400...0010 | cat-001         | Starbucks → Blue Bottle
```

---

## Key Takeaways

1. **Multi-Turn Confirmation**: Agent asks for confirmation after saving, enabling 2-turn interaction
2. **Intent Detection**: Uses `gemini-2.5-flash-lite` for efficient intent classification
3. **Seamless Corrections**: Users can provide corrections in natural Vietnamese
4. **Budget Awareness**: Agent warns about budget limits and provides financial advice
5. **Learning Loop**: Corrections are stored as feedback for future improvements
6. **Error Handling**: Invalid input triggers helpful clarification messages

---

## Testing the Confirmation Flow Locally

```bash
# 1. Start API
uvicorn src.api.main:app --reload

# 2. Register user
curl -X POST http://localhost:8000/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Pass123!","first_name":"Nguyễn","last_name":"Văn A"}'

# 3. Get JWT token
curl -X POST http://localhost:8000/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d 'username=test@example.com&password=Pass123!'

# 4. Start chat session
curl -X POST http://localhost:8000/v1/chat/start \
  -H "Authorization: Bearer <your_jwt_token>" \
  -H "Content-Type: application/json"

# 5. Send expense message
curl -X POST http://localhost:8000/v1/chat/<session_id>/message \
  -H "Authorization: Bearer <your_jwt_token>" \
  -H "Content-Type: application/json" \
  -d '{"content":"Tôi mua cà phê 25000 tại Starbucks","message_type":"text"}'

# 6. Response will have asking_confirmation=true

# 7. Send confirmation/correction
curl -X POST http://localhost:8000/v1/chat/<session_id>/message \
  -H "Authorization: Bearer <your_jwt_token>" \
  -H "Content-Type: application/json" \
  -d '{"content":"Không, thông tin đó đúng rồi","message_type":"text"}'
```
