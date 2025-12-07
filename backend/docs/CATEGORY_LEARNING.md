# Category Learning Service - Auto-learn from User Corrections

## Tổng quan

Tính năng **Auto-learn from Corrections** cho phép agent MoniAgent tự động học và ghi nhớ những thay đổi về phân loại danh mục của người dùng. Khi người dùng sửa một danh mục được gợi ý sai, hệ thống sẽ:

1. **Trích xuất keywords** từ mô tả chi tiêu
2. **Tạo rules mới** để tự động phân loại đúng lần sau
3. **Sử dụng lịch sử feedback** để cải thiện gợi ý

## Luồng hoạt động

```
┌──────────────────────────────────────────────────────────────────┐
│                    USER nhập chi tiêu                            │
│                   "vừa đi taxi 25k"                              │
└──────────────────────┬───────────────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────────────┐
│               Agent phân loại ban đầu                            │
│           (LLM hoặc keyword rules)                               │
│                                                                  │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │  Gợi ý: "Mua sắm cá nhân" (sai)                         │   │
│   └─────────────────────────────────────────────────────────┘   │
└──────────────────────┬───────────────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────────────┐
│               USER sửa danh mục                                  │
│           "Đổi thành Đi lại"                                     │
└──────────────────────┬───────────────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────────────┐
│           CategoryLearningService.learn_from_correction()        │
│                                                                  │
│   1. Trích xuất keywords: ["taxi"]                              │
│   2. Tạo rule mới: "taxi" → "Đi lại" (confidence: 0.85)         │
│   3. Lưu CategorizationFeedback record                          │
└──────────────────────┬───────────────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────────────┐
│               LẦN SAU: USER nhập                                 │
│               "taxi 30k đi siêu thị"                             │
│                                                                  │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │  Agent tự động phân loại đúng: "Đi lại" ✅               │   │
│   │  (Dựa vào rule đã học)                                  │   │
│   └─────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────┘
```

## Các thành phần

### 1. CategoryLearningService

**File:** `backend/src/services/category_learning_service.py`

Các methods chính:

| Method | Mô tả |
|--------|-------|
| `extract_keywords_from_text(text)` | Trích xuất keywords từ text, loại bỏ stopwords và amount patterns |
| `learn_from_correction(...)` | Học từ correction và tạo rules mới |
| `get_suggestion_from_history(...)` | Gợi ý category dựa trên lịch sử corrections |
| `get_learning_statistics(...)` | Thống kê về việc học của agent |

### 2. CategorizationService (cập nhật)

**File:** `backend/src/services/categorization_service.py`

Các thay đổi:

- `suggest_category()`: Bây giờ kiểm tra cả feedback history nếu không có rule nào match
- `confirm_categorization()`: Tự động gọi `learn_from_correction()` khi user sửa category
- `_get_suggestion_from_feedback_history()`: Helper method mới để query feedback history

### 3. ExpenseProcessingService (cập nhật)

**File:** `backend/src/services/expense_processing_service.py`

- `_store_correction_learning()`: Bây giờ sử dụng `CategoryLearningService` để tự động tạo rules khi category được sửa

### 4. API Endpoints mới

**File:** `backend/src/api/v1/category_router.py`

| Endpoint | Method | Mô tả |
|----------|--------|-------|
| `/categories/learning/statistics` | GET | Xem thống kê learning của agent |
| `/categories/learning/rules` | GET | Xem tất cả rules đã học |

## Ví dụ sử dụng

### 1. Khi user sửa category

```python
# Trong CategorizationService.confirm_categorization()
result = service.confirm_categorization(
    user_id="user-123",
    expense_id="expense-456",
    category_id="cat-di-lai",  # Category mới được user chọn
    suggested_category_id="cat-mua-sam",  # Category cũ (sai)
    db_session=db,
    auto_learn=True  # Tự động học (mặc định True)
)

# Result sẽ bao gồm:
{
    "expense_id": "expense-456",
    "category_id": "cat-di-lai",
    "category_name": "Đi lại",
    "was_correction": True,
    "learning": {
        "keywords_learned": ["taxi"],
        "rules_created": 1,
        "message": "Learned 1 keywords for category 'Đi lại'"
    }
}
```

### 2. Xem thống kê learning

```bash
GET /api/v1/categories/learning/statistics

# Response:
{
    "status": "success",
    "total_rules": 175,
    "active_rules": 175,
    "total_feedback": 12,
    "corrections": 8,
    "confirmations": 4,
    "learning_rate": 66.67,
    "message": "Agent has learned 175 rules from 8 corrections"
}
```

## Vietnamese Stopwords

Các từ sau sẽ được loại bỏ khi trích xuất keywords:

```python
VIETNAMESE_STOPWORDS = {
    "của", "và", "là", "để", "cho", "với", "trong", "này", "đó", "có",
    "được", "một", "các", "những", "từ", "đến", "theo", "về", "như",
    "trên", "dưới", "sau", "trước", "khi", "nếu", "vì", "nhưng",
    "hoặc", "hay", "rồi", "vậy", "thì", "mà", "bị", "ra", "vào",
    "lên", "xuống", "đi", "đến", "vừa", "mới", "đã", "sẽ", "đang",
    "còn", "nữa", "quá", "rất", "lắm", "cũng", "chỉ", "tất", "cả",
    "k", "vnd", "đ", "vnđ", "đồng", "nghìn", "triệu", "tỷ",
}
```

## Xử lý xung đột

Khi một keyword đã được map sang category khác:

1. **Nếu user sửa**: Rule cũ sẽ được **cập nhật** để trỏ đến category mới
2. **Confidence được boost**: Nếu user xác nhận đúng, confidence có thể tăng lên

## Testing

Chạy test:

```bash
cd backend
python tests/test_category_learning.py
```

## Cấu hình

Các thông số có thể điều chỉnh trong `CategoryLearningService`:

| Thông số | Mặc định | Mô tả |
|----------|----------|-------|
| `min_length` | 2 | Độ dài tối thiểu của keyword |
| `confidence_threshold` | 0.85 | Confidence threshold cho rules mới |

## Lưu ý quan trọng

1. **Không fail toàn bộ operation**: Nếu learning thất bại, việc xác nhận category vẫn thành công
2. **Non-blocking**: Learning được thực hiện sau khi confirm category
3. **Idempotent**: Nếu rule đã tồn tại, chỉ boost confidence thay vì tạo mới
