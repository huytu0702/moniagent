# Phân tích và Đặc tả Use Case - MoniAgent

Tài liệu này cung cấp phân tích chi tiết và đặc tả các Use Case (trường hợp sử dụng) trong hệ thống MoniAgent, bao gồm cả tương tác Backend (AI Agent) và Frontend.

## 1. Tổng quan Actor (Tác nhân)

| Actor | Mô tả |
|-------|-------|
| **User (Người dùng)** | Người sử dụng ứng dụng để theo dõi chi tiêu, quản lý ngân sách và nhận tư vấn tài chính. |
| **AI Agent** | Trợ lý ảo thông minh (LangGraph) tương tác hội thoại, xử lý yêu cầu, trích xuất thông tin từ tin nhắn/ảnh. |
| **System (Hệ thống)** | Các dịch vụ Backend, Cơ sở dữ liệu, OCR Engine, API Services. |

---

## 2. Danh sách Use Case Chi tiết

### UC1: Ghi nhận chi tiêu qua tin nhắn (Text-to-Expense)
**Mô tả**: Người dùng nhập thông tin chi tiêu bằng ngôn ngữ tự nhiên, hệ thống tự động trích xuất và đề xuất lưu trữ.

*   **Pre-conditions**: Người dùng đã đăng nhập.
*   **Flow**:
    1.  User gửi tin nhắn (ví dụ: "Sáng nay ăn phở 50k", "Grab hết 30k").
    2.  AI Agent nhận diện ý định (Intent Detection) là báo cáo chi tiêu.
    3.  System phân tích văn bản để trích xuất:
        *   **Số tiền**: Xử lý đa dạng format (50k, 50.000, 50 nghìn...).
        *   **Merchant (Cửa hàng)**: Sử dụng LLM để nhận diện tên địa điểm/thương hiệu.
        *   **Thời gian**: Xử lý ngữ nghĩa (hôm nay, hôm qua, 25/12...).
    4.  System tự động phân loại (Auto-categorization) dựa trên:
        *   Từ khóa (Keyword rules) đã học từ lịch sử.
        *   LLM suy luận nếu không khớp từ khóa.
    5.  AI Agent phản hồi lại thông tin đã trích xuất ở trạng thái "Chờ xác nhận" (Pending).
*   **Post-conditions**: Thông tin chi tiêu được lưu tạm trong State, chờ user xác nhận (UC3).

### UC2: Ghi nhận chi tiêu qua hình ảnh (Image-to-Expense)
**Mô tả**: Người dùng tải lên ảnh hóa đơn, hệ thống dùng OCR để số hóa thông tin.

*   **Pre-conditions**: User đã đăng nhập, có file ảnh hóa đơn.
*   **Flow**:
    1.  User tải lên ảnh (hóa đơn siêu thị, biên lai...).
    2.  System (OCR Service) xử lý ảnh để lấy text thô.
    3.  System trích xuất các trường dữ liệu quan trọng:
        *   **Merchant Name**: Tên cửa hàng ở đầu hóa đơn.
        *   **Total Amount**: Tổng tiền thanh toán.
        *   **Date**: Ngày xuất hóa đơn.
    4.  System thực hiện Auto-categorization tương tự UC1.
    5.  AI Agent phản hồi kết quả trích xuất cho User.
*   **Post-conditions**: Thông tin hóa đơn được lưu tạm, chờ xác nhận.

### UC3: Xác nhận và Điều chỉnh thông tin (Review & Correction)
**Mô tả**: User xem lại thông tin hệ thống trích xuất và sửa đổi nếu sai sót trước khi lưu chính thức.

*   **Pre-conditions**: Có một giao dịch đang ở trạng thái Pending (từ UC1 hoặc UC2).
*   **Flow**:
    1.  AI Agent hiển thị thông tin: Số tiền, Cửa hàng, Ngày, Danh mục (dự đoán).
    2.  User có thể:
        *   **Xác nhận**: Gõ "ok", "lưu", "đúng rồi". -> Hệ thống lưu vào DB (Expense Table).
        *   **Chỉnh sửa**: Gõ yêu cầu sửa (ví dụ: "Sửa tiền thành 60k", "Đổi sang mục Ăn uống").
            *   AI Agent phân tích câu lệnh sửa đổi.
            *   Cập nhật lại State và hiển thị lại thông tin mới.
        *   **Hủy**: Gõ "hủy" -> Bỏ qua giao dịch.
*   **Logic Tự học (Learning)**: Nếu User sửa lại Danh mục (Category) khác với đề xuất ban đầu, hệ thống sẽ ghi nhớ từ khóa liên quan để cải thiện lần sau (UC6).

### UC4: Quản lý ngân sách & Cảnh báo (Budget Checking)
**Mô tả**: Hệ thống tự động kiểm tra hạn mức ngân sách ngay sau khi lưu chi tiêu mới và đưa ra cảnh báo nếu vượt ngưỡng.

*   **Trigger**: Gọi tự động trong phương thức `save_expense` của `ExpenseProcessingService` sau khi chi tiêu đã được cam kết (commit) vào Database.
*   **Flow**:
    1.  **Tính toán chi tiêu thực tế**:
        *   Hệ thống (`BudgetManagementService`) truy vấn tổng tiền các chi tiêu (`Category`) trong kỳ hiện tại (mặc định là tháng hiện tại) từ Database.
        *   Cộng thêm số tiền của chi tiêu vừa mới lưu.
    2.  **Kiểm tra hạn mức**:
        *   Lấy thông tin `Budget` cấu hình cho `Category` đó.
        *   Tính `% đã dùng` = `(Tổng chi tiêu thực tế + Chi tiêu mới) / Hạn mức`.
    3.  **Logic Cảnh báo (Alert Logic)**:
        *   **Cấp độ cao (High)**: Nếu `% đã dùng >= 100%`.
            *   Message: "Bạn đã vượt quá ngân sách cho danh mục {category_name}!"
        *   **Cấp độ trung bình (Medium)**: Nếu `% đã dùng >= alert_threshold` (mặc định 80%).
            *   Message: "Bạn đang tiến gần đến ngân sách cho danh mục {category_name}."
    4.  **Phản hồi User**:
        *   Message cảnh báo được gán kèm vào phản hồi xác nhận lưu thành công ("✅ Đã lưu...").
        *   Hiển thị dưới dạng dòng thông báo có icon cảnh báo: `⚠️ [Nội dung cảnh báo]`.

### UC5: Tư vấn tài chính (Financial Advice)
**Mô tả**: User chủ động hỏi lời khuyên hoặc yêu cầu báo cáo tình hình tài chính.

*   **Flow**:
    1.  User hỏi: "Tình hình chi tiêu tháng này thế nào?", "Cho tôi lời khuyên tiết kiệm".
    2.  AI Agent phát hiện ý định "Advice Request".
    3.  System tổng hợp dữ liệu chi tiêu (theo ngày/tuần/tháng).
    4.  System phân tích xu hướng (Trend Analysis):
        *   So sánh với kỳ trước.
        *   Tìm danh mục tiêu nhiều nhất.
    5.  AI Agent sinh câu trả lời tư vấn chi tiết, có thể kèm biểu đồ (nếu trên UI hỗ trợ) hoặc text định dạng Markdown.

### UC6: Hệ thống tự học phân loại (Category Learning)
**Mô tả**: Cơ chế ngầm (Background) giúp AI thông minh hơn qua từng lần tương tác.

*   **Trigger**: Khi User sửa lại Category trong UC3.
*   **Flow**:
    1.  Hệ thống so sánh `original_category` (hệ thống đoán) và `final_category` (người dùng chốt).
    2.  Nếu khác nhau, System gọi `CategoryLearningService`.
    3.  Lưu Rules mới vào DB: User X, Keyword "Y" -> Category Z.
    4.  Lần sau khi gặp Keyword "Y", hệ thống sẽ ưu tiên map vào Category Z thay vì dùng LLM đoán chung chung.

### UC7: Cấu hình ngân sách (Budget Configuration) - Frontend
**Mô tả**: User thiết lập hạn mức chi tiêu cho từng danh mục qua giao diện Dashboard.

*   **Component**: `BudgetSettings`
*   **Flow**:
    1.  User truy cập màn hình Cài đặt / Ngân sách.
    2.  Hệ thống load danh sách Categories và Ngân sách hiện tại.
    3.  User nhập số tiền giới hạn cho từng mục (ví dụ: Ăn uống 3tr/tháng).
    4.  User nhấn Lưu -> System update DB.
    5.  Dữ liệu này sẽ được dùng cho UC4.

### UC8: Xem Báo cáo tổng quan (Dashboard View) - Frontend
**Mô tả**: User xem biểu đồ và thống kê tổng quan.

*   **Component**: `ExpenseDashboard`, `ExpenseChart`
*   **Flow**:
    1.  User vào trang chủ.
    2.  Hệ thống hiển thị:
        *   Tổng chi tiêu tháng này.
        *   Biểu đồ tròn/cột phân bổ theo danh mục.
        *   Danh sách giao dịch gần đây (`RecentTransaction`).
        *   Trạng thái ngân sách (thanh tiến trình chi tiêu).

## 3. Kiến trúc luồng dữ liệu (Data Flow)

1.  **Input**: User Input (Text/Image) -> Frontend (`ChatInterface`) -> API Backend.
2.  **Processing**:
    *   `LangGraphAIAgent`: Điều phối luồng, quản lý State hội thoại.
    *   `ExpenseProcessingService`: Logic nghiệp vụ chính (Extract, Save).
    *   `CategorizationService` & `CategoryLearningService`: Phân loại thông minh.
3.  **Storage**: PostgreSQL (lưu Expenses, Categories, Budgets, Correction Rules).
4.  **Feedback**: AI Agent trả về Message -> Frontend hiển thị đoạn chat.

## 4. Điểm đặc biệt (Highlights)
*   **Hybrid Intelligence**: Kết hợp Rule-based (nhanh, chính xác với thói quen cũ) và LLM (linh hoạt với dữ liệu mới).
*   **Adaptive Flow**: Luồng hội thoại có khả năng tạm dừng (Interrupt) để hỏi ý kiến người dùng, không tự động lưu sai.
*   **Multi-modal**: Hỗ trợ cả văn bản và hình ảnh.
