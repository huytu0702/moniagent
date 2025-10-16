# Phân Tích Khả Năng AI Agent & Lộ Trình Cải Tiến

## Tóm Tắt Tình Hình

**Trạng Thái Hiện Tại**: ⚠️ **Triển Khai AI Agent Một Phần**
- Hệ thống có các tính năng AI cơ bản nhưng thiếu hành vi agent tự chủ thực sự
- Đã triển khai: Tạo nội dung do AI hỗ trợ (OCR, phân loại, lời khuyên)
- Thiếu: Điều phối thông minh, suy luận đa bước, ra quyết định chủ động, nhận thức ngữ cảnh

**Mục Tiêu**: Chuyển đổi thành **AI Agent Toàn Năng** tự động quản lý tài chính người dùng với xác nhận của con người

---

## 1. ĐÁNH GIÁ KHÁC NĂNG AI HIỆN TẠI

### ✅ CÓ Những Gì (Nền Tảng Tốt)

| Thành Phần | Trạng Thái | Chi Tiết |
|-----------|-----------|---------|
| **Xử Lý OCR** | ✅ Hoàn tất | Gemini 2.5 Flash trích xuất: tên cửa hàng, ngày, tổng số tiền |
| **Phân Loại Chi Tiêu** | ✅ Hoàn tất | Đề xuất danh mục với điểm tin cậy; học từ sửa chữa của người dùng |
| **Lời Khuyên Tài Chính** | ✅ Hoàn tất | Tạo đề xuất chi tiêu dựa trên các mẫu |
| **Tích Hợp Mô Hình AI** | ✅ Hoàn tất | Gemini API được cấu hình; dự phòng mặc định nếu không khả dụng |
| **Vòng Phản Hồi** | ✅ Hoàn tất | Ghi lại sửa chữa của người dùng để học tập |
| **Cảnh Báo Ngân Sách** | ✅ Hoàn tất | Các tác vụ được lên lịch để phát hiện vi phạm ngân sách |

### ❌ THIẾU Những Gì (Hành Vi Agent Thực Sự)

| Tính Năng Thiếu | Tác Động | Mức Độ Ưu Tiên |
|-----------------|---------|---|
| **Ra Quyết Định Tự Chủ** | Agent chỉ đề xuất; không quyết định | CAO |
| **Điều Phối Đa Bước** | Không phối hợp quy trình làm việc | CAO |
| **Nhận Thức Ngữ Cảnh** | Không ghi nhớ sở thích/mẫu người dùng | CAO |
| **Hành Động Chủ Động** | Chỉ phản ứng với yêu cầu; không bao giờ chủ động | CAO |
| **Định Tuyến Thông Minh** | Không có cây quyết định cho phân loại chi tiêu | TRUNG |
| **Phát Hiện Bất Thường** | Không xác định các mẫu chi tiêu bất thường | TRUNG |
| **Phân Tích Dự Đoán** | Không dự báo hoặc phân tích xu hướng | TRUNG |
| **Hội Thoại Đa Lượt** | Không thể duy trì ngữ cảnh hội thoại | TRUNG |
| **Tối Ưu Hóa Mục Tiêu** | Không tối ưu hóa theo mục tiêu tài chính của người dùng | TRUNG |
| **Học Tập & Thích Ứng** | Không cá nhân hóa theo thời gian | TRUNG |

---

## 2. KHOẢNG TRỐNG KIẾN TRÚC

### Kiến Trúc Hiện Tại
```
Yêu Cầu Người Dùng
    ↓
Điểm Cuối API
    ↓
Lớp Dịch Vụ (Gọi AI đơn giản)
    ↓
Lệnh Gọi API AI (Một lần)
    ↓
Phản Hồi
```

### Những Gì Cần Thiết (Kiến Trúc Agent)
```
Yêu Cầu/Sự Kiện Người Dùng
    ↓
Bộ Điều Phối Agent
    ├─→ Trình Quản Lý Ngữ Cảnh (hồ sơ người dùng, lịch sử)
    ├─→ Công Cụ Ra Quyết Định (suy luận đa bước)
    ├─→ Bộ Định Tuyến Công Cụ (dịch vụ nào cần gọi)
    ├─→ Trình Quản Lý Bộ Nhớ (lịch sử hội thoại, sở thích)
    └─→ Bộ Thực Hiện Hành Động (ra quyết định, ghi lại phản hồi)
    ↓
Phản Hồi + Nhật Ký Hành Động
```

---

## 3. NHỮNG CẢI TIẾN CHÍNH CẦN THIẾT

### Giai Đoạn 1: Nền Tảng Agent (Tuần 1-2)

#### 1.1 **Tạo Bộ Điều Phối Agent** (`src/core/agent.py`)
```python
class FinancialAgent:
    - __init__(user_id, context)
    - process_expense(expense_data) → Decision
    - optimize_budget() → Recommendations
    - detect_anomalies() → Alert
    - get_conversation_context() → History
```

**Tại sao**: Trí tuệ trung tâm phối hợp tất cả các quyết định AI thay vì các lệnh gọi dịch vụ rải rác.

#### 1.2 **Triển Khai Trình Quản Lý Ngữ Cảnh** (`src/core/context.py`)
Lưu trữ và truy xuất:
- Mục tiêu tài chính của người dùng
- Thói quen chi tiêu theo danh mục
- Quy tắc phân loại ưu tiên
- Các tương tác AI trước đây (lịch sử hội thoại)
- Hồ sơ rủi ro

**Tại sao**: Agent cần "nhớ" các mẫu người dùng để ra quyết định thông minh.

#### 1.3 **Thêm Lưu Trữ Bộ Nhớ**
Tạo bảng mới: `ai_conversation_history`
- `id`, `user_id`, `interaction_type`, `input_data`, `ai_response`, `user_feedback`, `timestamp`

**Tại sao**: Cho phép hội thoại đa lượt và học tập được cá nhân hóa.

---

### Giai Đoạn 2: Ra Quyết Định Thông Minh (Tuần 3-4)

#### 2.1 **Công Cụ Phân Loại Thông Minh** (`src/services/smart_categorization_service.py`)

**Hiện Tại**: Phù hợp mẫu dựa trên quy tắc
**Cải Tiến**: Cây quyết định với ngữ cảnh
```
Quy Tắc:
IF độ tin cậy >= 0.9 THEN tự động chấp thuận
IF độ tin cậy 0.7-0.9 AND phù hợp_mẫu_người_dùng THEN đề xuất + học
IF độ tin cậy < 0.7 THEN hỏi người dùng
IF số_tiền_bất_thường THEN đánh dấu_để_xem_xét
```

#### 2.2 **Phân Loại Chi Tiêu Có Ngữ Cảnh**
- Học các mẫu nhà cung cấp điển hình của người dùng
- Phát hiện mơ hồ danh mục (ví dụ: "trạm xăng" → nhiên liệu HOẶC mua hàng tiện lợi)
- Đề xuất dựa trên thời gian, số tiền, ngày trong tuần

**Ví Dụ**:
```
Starbucks $5 vào sáng thứ Ba → Cà phê (độ tin cậy cao)
Starbucks $45 vào tối thứ Sáu → Đồ ăn/Giải trí (độ tin cậy thấp hơn, hỏi)
```

#### 2.3 **Phát Hiện Bất Thường** (`src/services/anomaly_detection_service.py`)
- Đánh dấu chi tiêu bất thường: 5 lần số tiền bình thường trong danh mục
- Phát hiện thay đổi danh mục: chi tiêu thấp thường xuyên, đột ngột cao
- Xác định các mẫu nhà cung cấp mới

---

### Giai Đoạn 3: Hành Vi Agent Chủ Động (Tuần 5-6)

#### 3.1 **Agent Tối Ưu Hóa Ngân Sách**
Thay vì chỉ cảnh báo, đề xuất hành động:
- "Chi tiêu ăn uống là 120% ngân sách. Gợi ý 5 nhà hàng chi phí thấp thay thế"
- "Bạn sắp chi tiêu vượt quá $200. Giảm $15/tuần hoặc điều chỉnh ngân sách"

#### 3.2 **Kế Hoạch Hướng Theo Mục Tiêu**
Bảng mới: `user_financial_goals`
- Mục tiêu (tiết kiệm $500/tháng, giảm ăn uống 30%, v.v.)
- Agent tự động:
  - Theo dõi tiến độ
  - Đề xuất hành động
  - Cảnh báo khi lệch hướng
  - Tối ưu hóa các con đường đạt mục tiêu

#### 3.3 **Phân Tích Dự Đoán**
- Dự báo chi tiêu tháng tới
- Cảnh báo trước khi ngưỡng ngân sách
- Gợi ý chiến lược chi tiêu tối ưu

---

### Giai Đoạn 4: Khả Năng Agent Nâng Cao (Tuần 7-8)

#### 4.1 **Công Cụ Hội Thoại Đa Lượt**
```
Người dùng: "Tại sao chi tiêu của tôi cao như vậy tháng này?"
Agent: "Danh mục ăn uống cao hơn bình thường 40% ($600 vs $430 trung bình)"
Người dùng: "Tôi nên làm gì?"
Agent: "Tùy Chọn 1: Nấu ăn nhiều hơn (5 bữa tối ít hơn = -$150)
         Tùy Chọn 2: Tìm nhà hàng rẻ hơn (trung bình $15→$12)
         Tùy Chọn 3: Cả hai để tuân thủ ngân sách đầy đủ"
Người dùng: "Tôi sẽ thử tùy chọn 1"
Agent: "Tôi sẽ theo dõi. Xác nhận tiết kiệm vào tuần tới."
```

Yêu cầu: Lưu trữ lịch sử hội thoại + truy xuất

#### 4.2 **Học Tập Sở Thích Người Dùng**
- Theo dõi những khuyến nghị nào mà người dùng chấp nhận
- Điều chỉnh tạo lời khuyên theo phong cách giao tiếp ưa thích
- Ghi nhớ các quyết định trước để tránh các đề xuất dư thừa

#### 4.3 **Lọc Cộng Tác**
- Học từ hành vi của những người dùng tương tự
- "Người dùng như bạn đã giảm ăn uống bằng cách chuẩn bị bữa ăn"

---

## 4. LỘ TRÌNH TRIỂN KHAI

### Chiến Thắng Nhanh (1-2 tuần, tác động cao)

1. **Thêm Lớp Bộ Điều Phối Agent**
   - Tệp: `backend/src/core/agent.py`
   - Định tuyến quyết định qua agent thay vì trực tiếp đến các dịch vụ
   - Phụ thuộc: Không có (bao bọc các dịch vụ hiện có)

2. **Lưu Trữ Lịch Sử Hội Thoại**
   - Tệp: `backend/src/models/conversation.py`
   - Di chuyển: Thêm bảng `ai_conversation_history`
   - Điểm cuối: `GET /api/v1/agent/conversation-history`

3. **Trình Quản Lý Ngữ Cảnh Nâng Cao**
   - Tệp: `backend/src/services/user_context_service.py`
   - Tải hồ sơ người dùng, mục tiêu, sở thích theo yêu cầu
   - Bộ nhớ cache để có hiệu suất

### Trung Hạn (3-4 tuần, tính năng cốt lõi)

4. **Phân Loại Thông Minh Với Ngữ Cảnh**
   - Cập nhật `categorization_service.py` để sử dụng Agent
   - Thêm quy tắc cây quyết định
   - Triển khai ngưỡng độ tin cậy

5. **Dịch Vụ Phát Hiện Bất Thường**
   - Tệp: `backend/src/services/anomaly_detection_service.py`
   - Phân tích thống kê các mẫu chi tiêu
   - Phát hiện ngoại lệ dựa trên Z-score

6. **Tối Ưu Hóa Dựa Trên Mục Tiêu**
   - Tệp: `backend/src/models/financial_goal.py`
   - Tệp: `backend/src/services/goal_optimizer_service.py`
   - Điểm cuối: `POST /api/v1/agent/goals`

### Dài Hạn (5+ tuần, tính năng nâng cao)

7. **Công Cụ Hội Thoại Đa Lượt**
   - Tệp: `backend/src/services/conversation_service.py`
   - Quản lý hội thoại trạng thái
   - Phản hồi nhận thức ngữ cảnh

8. **Phân Tích Dự Đoán**
   - Tệp: `backend/src/services/predictive_service.py`
   - Dự báo chi tiêu
   - Phân tích xu hướng

---

## 5. CÁC ĐIỂM CUỐI API MỚI CHO AGENT

### Hội Thoại Agent
```
POST /api/v1/agent/ask
Body: { "question": "Tại sao chi tiêu của tôi cao?", "context": {...} }
Response: { "answer": "...", "recommendations": [...], "conversation_id": "..." }

GET /api/v1/agent/conversation-history/{conversation_id}
Response: [{"turn": 1, "user": "...", "agent": "..."}, ...]

POST /api/v1/agent/feedback
Body: { "interaction_id": "...", "accepted": true/false, "notes": "..." }
```

### Quyết Định Agent
```
POST /api/v1/agent/categorize-smart
Body: { "expense": {...} }
Response: { "category": "...", "confidence": 0.95, "reasoning": "...", "alternative_categories": [...] }

GET /api/v1/agent/anomalies
Response: [{"type": "high_spending", "category": "dining", "severity": "medium"}]
```

### Mục Tiêu Agent
```
POST /api/v1/agent/goals
Body: { "goal_type": "save", "amount": 500, "period": "monthly", "target_categories": ["dining"] }

GET /api/v1/agent/goals/{goal_id}/progress
Response: { "goal": "...", "progress": 0.65, "on_track": true, "suggestions": [...] }
```

---

## 6. CÁC BẢNG CƠ SỬ DỮ LIỆU CẦN THÊM

### Bảng Mới

```sql
-- Lịch sử hội thoại cho các cuộc trò chuyện đa lượt
CREATE TABLE ai_conversation (
  id UUID PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES users(id),
  conversation_id UUID NOT NULL,
  turn_number INT,
  user_input TEXT,
  agent_response TEXT,
  reasoning TEXT,
  user_feedback BOOLEAN,
  created_at TIMESTAMP
);

-- Mục tiêu tài chính
CREATE TABLE financial_goals (
  id UUID PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES users(id),
  goal_type VARCHAR(50), -- 'save', 'spend_limit', 'category_target'
  target_amount DECIMAL,
  target_category_id UUID REFERENCES categories(id),
  period VARCHAR(20), -- 'weekly', 'monthly', 'annual'
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);

-- Theo dõi tiến độ mục tiêu
CREATE TABLE goal_progress (
  id UUID PRIMARY KEY,
  goal_id UUID REFERENCES financial_goals(id),
  current_amount DECIMAL,
  progress_percent FLOAT,
  on_track BOOLEAN,
  last_updated TIMESTAMP
);

-- Bộ nhớ cache mẫu chi tiêu (cho ML)
CREATE TABLE spending_patterns (
  id UUID PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES users(id),
  category_id UUID REFERENCES categories(id),
  avg_monthly DECIMAL,
  std_dev DECIMAL,
  p90_spending DECIMAL,
  last_updated TIMESTAMP
);
```

---

## 7. ĐẶC BIỆT: MẪU TRIỂN KHAI FLOW AGENT THÔNG MINH

```python
# backend/src/core/agent.py

class FinancialAgent:
    def __init__(self, user_id: str, db: Session):
        self.user_id = user_id
        self.db = db
        self.context = UserContextService(user_id, db).get_context()
        self.memory = ConversationMemory(user_id, db)
        
    def process_expense(self, expense: Expense) -> AgentDecision:
        """Phân loại chi tiêu thông minh với ngữ cảnh"""
        
        # 1. Kiểm tra sở thích người dùng
        user_rules = self.context.get_preferred_categories(expense.store_name)
        if user_rules and self.context.confidence_threshold_met(user_rules):
            return AgentDecision(
                category=user_rules['category'],
                confidence=0.95,
                action='auto_categorize',
                reasoning=f"Phù hợp mẫu người dùng: {user_rules['reason']}"
            )
        
        # 2. Phân loại AI
        ai_suggestion = CategorizationService().suggest_category(
            self.user_id, expense.id, self.db
        )
        
        # 3. Kiểm tra bất thường
        if AnomalyDetectionService().is_anomalous(expense, self.context):
            return AgentDecision(
                category=ai_suggestion['category'],
                confidence=ai_suggestion['confidence'],
                action='ask_user',
                reasoning=f"Phát hiện số tiền bất thường. Bình thường cho {expense.store_name}: ${self.context.avg_spend[expense.store_name]}"
            )
        
        # 4. Mặc định: đề xuất với ngưỡng độ tin cậy
        if ai_suggestion['confidence'] >= 0.8:
            return AgentDecision(
                category=ai_suggestion['category'],
                confidence=ai_suggestion['confidence'],
                action='suggest_with_alternatives',
                reasoning=ai_suggestion['reason']
            )
        else:
            return AgentDecision(
                category=ai_suggestion['category'],
                confidence=ai_suggestion['confidence'],
                action='ask_user',
                reasoning="Độ tin cậy thấp, yêu cầu xác nhận người dùng"
            )
```

---

## Kết Luận

Backend có các khả năng AI nền tảng vững chắc nhưng cần chuyển đổi thành một **AI Agent Thực Sự** với:
- ✅ Ra quyết định tự chủ
- ✅ Nhận thức ngữ cảnh
- ✅ Đề xuất chủ động
- ✅ Trí tuệ đa lượt
- ✅ Học tập liên tục

**Các Bước Tiếp Theo**: Bắt đầu với Giai Đoạn 1 (Bộ Điều Phối Agent) để thiết lập trung tâm trí tuệ tập trung, sau đó xếp lớp ra quyết định thông minh và các hành vi chủ động.
