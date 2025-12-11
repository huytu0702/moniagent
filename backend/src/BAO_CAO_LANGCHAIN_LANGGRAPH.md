# BÁO CÁO CƠ SỞ LÝ THUYẾT VÀ CÔNG NGHỆ LANGCHAIN & LANGGRAPH TRONG MONIAGENT

## 1. CƠ SỞ LÝ THUYẾT (THEORETICAL BASIS)

### 1.1. Agentic AI
Agentic AI là bước tiến hóa tiếp theo của Generative AI (GenAI). Thay vì chỉ phản hồi câu hỏi (chatbot), các AI Agent có khả năng:
- **Tự chủ (Autonomy)**: Tự ra quyết định về các bước cần thực hiện để đạt mục tiêu.
- **Sử dụng công cụ (Tool Use)**: Tương tác với thế giới bên ngoài (database, API, search) để thực hiện hành động.
- **Lập kế hoạch (Planning)**: Phân rã nhiệm vụ phức tạp thành các bước nhỏ.
- **Ghi nhớ (Memory)**: Duy trì ngữ cảnh qua nhiều lượt tương tác.

### 1.2. LangChain Framework
LangChain là framework mã nguồn mở phổ biến nhất để phát triển các ứng dụng dựa trên LLM (Large Language Module). Các thành phần cốt lõi được sử dụng trong Moniagent:
- **Model I/O**: Giao diện chuẩn hóa cho các LLM (trong hệ thống là Google Gemini).
- **Prompts**: Quản lý và tối ưu hóa câu lệnh đầu vào cho mô hình.
- **Tools**: Đóng gói các hàm Python thành công cụ mà AI có thể gọi (ví dụ: `FinancialAdviceTool`, `BudgetCheckTool`).

### 1.3. LangGraph - Kiến trúc đồ thị cho AI
LangGraph là thư viện xây dựng trên LangChain, cho phép tạo ra các ứng dụng AI có trạng thái (stateful) và vòng lặp (cyclic) - điều mà các chuỗi (chains) tuyến tính truyền thống (DAG) không làm được.

Các đặc điểm nổi bật của LangGraph:
- **StateGraph**: Mô hình hóa ứng dụng dưới dạng đồ thị trạng thái, nơi các node là các hàm xử lý và edge là các chuyển đổi.
- **Cyclic Flows**: Hỗ trợ các vòng lặp (loop), rất quan trọng cho quy trình sửa lỗi (review-revise) của Agent.
- **Persistence (Checkpointer)**: Tự động lưu trạng thái của đồ thị, cho phép "nhớ" ngữ cảnh giữa các request HTTP.
- **Human-in-the-loop**: Khả năng tạm dừng (interrupt) quy trình để chờ phản hồi từ con người, sau đó tiếp tục từ đúng điểm dừng.

---

## 2. CÔNG NGHỆ VÀ KIẾN TRÚC TRONG MONIAGENT

Trong hệ thống Moniagent, chúng tôi sử dụng LangGraph để quản lý luồng hội thoại phức tạp của trợ lý tài chính, đặc biệt là quy trình xác nhận và chỉnh sửa thông tin chi tiêu.

### 2.1. Kiến trúc State (AgentState)
Toàn bộ ngữ cảnh của Agent được lưu trong `AgentState` (kế thừa `TypedDict`), đảm bảo tính nhất quán dữ liệu giữa các bước:

```python
class AgentState(TypedDict):
    # Lịch sử hội thoại
    messages: Annotated[List[BaseMessage], operator.add]
    user_id: str
    session_id: str
    
    # Trạng thái trích xuất chi tiêu
    extracted_expense: Dict          # Dữ liệu thô từ AI
    saved_expense: Dict              # Dữ liệu chuẩn hóa chờ lưu
    
    # Trạng thái luồng xác nhận (Human-in-the-loop)
    asking_confirmation: bool        # Đang chờ user xác nhận?
    user_confirmation_response: str  # Câu trả lời của user
    
    # Trạng thái chỉnh sửa
    wants_update: bool               # User có muốn sửa không?
    corrections: Dict                # Các trường thông tin cần sửa
    
    # Trạng thái tư vấn
    budget_warning: Dict
    financial_advice: Dict
```

### 2.2. Sơ đồ luồng xử lý (Graph Topology)

Luồng xử lý của Moniagent được thiết kế như một máy trạng thái hữu hạn (Finite State Machine):

1.  **START (Entry Point)**: `extract_expense`
2.  **Node: `extract_expense`**:
    *   Sử dụng Gemini 2.5 Flash để trích xuất thông tin từ văn bản hoặc hình ảnh hóa đơn.
    *   *Condition*: Nếu là yêu cầu lời khuyên -> sang `generate_advice`. Nếu có dữ liệu chi tiêu -> sang `prepare_confirmation`. Nếu không hiểu -> dùng `llm_call` để chat thông thường.
3.  **Node: `prepare_confirmation`**:
    *   Chuẩn hóa dữ liệu (ngày tháng, danh mục).
    *   Chuẩn bị bản ghi tạm (pending expense).
4.  **Node: `ask_confirmation` (INTERRUPT)**:
    *   Tạo thông báo xác nhận gửi user.
    *   **QUAN TRỌNG**: Gọi lệnh `interrupt()`. Hệ thống sẽ TẠM DỪNG tại đây, trả kết quả về Frontend và giải phóng tài nguyên. Trạng thái được lưu vào Database/Memory.
5.  **Resume & Routing**:
    *   Khi user phản hồi, hệ thống khôi phục trạng thái và chạy tiếp.
    *   *Condition*:
        *   User đồng ý ("ok", "lưu") -> sang `save_expense`.
        *   User muốn sửa ("sửa lại tiền") -> sang `detect_update_intent`.
        *   User hủy ("không lưu") -> sang `handle_cancel`.
6.  **Node: `detect_update_intent`**:
    *   Dùng AI (Gemini Flash Lite) để phân tích ý định sửa đổi của user (Sửa trường nào? Giá trị mới là gì?).
7.  **Answer Handling**:
    *   Nếu có chỉnh sửa chính xác -> sang `process_update`.
    *   Sau khi `process_update`, quay lại `ask_confirmation` (Tạo thành vòng lặp **Loop** cho đến khi user hài lòng).
8.  **Node: `save_expense`**:
    *   Lưu vào Supabase.
    *   Kích hoạt `CategoryLearningService` nếu user sửa danh mục để AI học hỏi.
    *   Kiểm tra ngân sách -> Nếu vượt ngân sách -> sang `generate_advice`.

### 2.3. Cơ chế Human-in-the-loop
Moniagent triển khai mô hình "Wait-for-confirmation" tiên tiến:
- Hệ thống không tự động lưu chi tiêu sau khi trích xuất.
- Sử dụng `checkpointer=InMemorySaver()` (trong môi trường dev) hoặc Postgres checkpointer (prod) để bền vững hóa state.
- **Cơ chế Interrupt**: Cho phép tách rời quá trình xử lý AI (backend) và tương tác người dùng (frontend). Khi user nhập liệu ở Frontend, một request mới được gửi kèm `thread_id`, Backend sẽ `resume` đồ thị từ điểm dừng.

### 2.4. Tối ưu hóa mô hình (Model Optimization)
Hệ thống sử dụng chiến lược đa mô hình (Multi-model strategy):
- **Gemini 2.5 Flash**: Dùng cho các tác vụ chính (Extraction, Advice) cần độ chính xác cao và khả năng xử lý đa phương thức (ảnh hóa đơn).
- **Gemini 2.5 Flash Lite**: Dùng cho tác vụ `detect_update_intent` (phân tích ý định sửa) để tối ưu tốc độ phản hồi và chi phí.

#### 2.4.1. Chi tiết các tác vụ sử dụng Gemini 2.5 Flash Lite
Sau khi phân tích mã nguồn, chúng tôi xác định `Gemini 2.5 Flash Lite` được sử dụng chuyên biệt cho các tác vụ "nhẹ" (lightweight), yêu cầu độ trễ thấp và xử lý logic đơn giản:

1.  **Phân tích ý định sửa đổi (Intent Detection)**
    *   *File*: `src/core/langgraph_agent.py`
    *   *Mô tả*: Khi người dùng phản hồi tin nhắn xác nhận (ví dụ: "sửa lại giá thành 50k"), Lite model phân tích văn bản để xác định:
        *   User có muốn sửa không? (`wants_update`: true/false)
        *   User muốn sửa trường nào? (amount, date, merchant_name)
    *   *Lý do*: Tác vụ này là bài toán phân loại/trích xuất đơn giản, Lite model xử lý nhanh hơn đáng kể so với bản chuẩn, giúp trải nghiệm chat mượt mà.

2.  **Trích xuất tên cửa hàng (Merchant Name Extraction)**
    *   *File*: `src/services/expense_processing_service.py`
    *   *Mô tả*: Trích xuất tên thực thể (NER) từ văn bản nhập liệu thô (ví dụ: từ "mua cafe highland" -> "Highland Coffee").
    *   *Lý do*: Chỉ tập trung vào một thực thể duy nhất, không cần khả năng suy luận phức tạp.

3.  **Trích xuất gợi ý (Recommendation Extraction)**
    *   *File*: `src/services/financial_advice_service.py`
    *   *Mô tả*: Từ một đoạn văn bản lời khuyên dài, trích xuất ra 3 gạch đầu dòng ngắn gọn, hành động được (actionable items) để hiển thị trên UI.
    *   *Lý do*: Tác vụ tóm tắt/định dạng lại (reformatting) văn bản, phù hợp với năng lực của Lite model.

### 2.5. Các Công nghệ hỗ trợ
- **Pydantic**: Định nghĩa Schema cho dữ liệu đầu ra của AI (Structured Output), đảm bảo tính nhất quán (ví dụ: `ExpenseExtractionTool`).
- **SQLAlchemy & Supabase**: Lưu trữ dữ liệu nghiệp vụ và tích hợp với Vector Store cho các tính năng tìm kiếm ngữ nghĩa sau này.
