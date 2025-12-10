# CƠ SỞ LÝ THUYẾT VÀ CÔNG NGHỆ CỦA MONIAGENT

## TỔNG QUAN

Moniagent là một ứng dụng quản lý tài chính cá nhân thông minh sử dụng công nghệ AI để tự động hóa việc phân tích và quản lý chi tiêu. Hệ thống được xây dựng theo kiến trúc microservices với frontend và backend tách biệt, tích hợp các công nghệ AI hiện đại để xử lý ngôn ngữ tự nhiên và nhận dạng hình ảnh.

## KIẾN TRÚC HỆ THỐNG

### 1. Kiến trúc tổng thể
- **Frontend**: Next.js 15 với React 18, TypeScript
- **Backend**: FastAPI với Python 3.10+
- **Database**: Supabase (PostgreSQL) cho dữ liệu người dùng và chi tiêu
- **AI/ML**: Google Gemini 2.5, LangChain, LangGraph
- **Authentication**: JWT tokens với bcrypt

### 2. Microservices Architecture
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend      │    │   AI Services   │
│   (Next.js)     │◄──►│   (FastAPI)     │◄──►│  (Gemini AI)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       ▼                       │
         │              ┌─────────────────┐              │
         │              │   Database      │              │
         │              │  (Supabase)     │              │
         │              └─────────────────┘              │
         └───────────────────────────────────────────────┘
```

## CÔNG NGHỆ FRONTEND

### 1. Framework và Core Technologies
- **Next.js 15**: React framework với SSR/SSG capabilities
- **React 18.3.1**: UI library với Concurrent Features
- **TypeScript 5**: Static typing cho better development experience
- **Tailwind CSS 4.1.9**: Utility-first CSS framework

### 2. UI Components và Design System
- **Radix UI**: Headless components cho accessible UI
  - Dialog, Dropdown, Select, Tabs, Toast, v.v.
- **Lucide React**: Icon library
- **Shadcn/ui**: Component library built on Radix UI
- **CVA (Class Variance Authority)**: Component variant management

### 3. State Management và Data Fetching
- **React Context**: Global state management
- **React Hook Form**: Form handling với Zod validation
- **Custom API Client**: HTTP client với error handling
- **Middleware**: Authentication và request interception

### 4. Frontend Package Structure
```json
{
  "core": ["next", "react", "typescript"],
  "ui": ["@radix-ui/*", "tailwindcss", "lucide-react"],
  "forms": ["react-hook-form", "@hookform/resolvers", "zod"],
  "data": ["recharts", "date-fns"],
  "utils": ["clsx", "tailwind-merge"]
}
```

## CÔNG NGHỆ BACKEND

### 1. Framework và Core
- **FastAPI 0.100+**: Modern Python web framework với automatic OpenAPI
- **Python 3.10+**: Language version với type hints support
- **Pydantic 2.0+**: Data validation và serialization
- **SQLAlchemy**: ORM cho database operations

### 2. Database và Storage
- **Supabase**: Backend-as-a-Service với PostgreSQL
  - Real-time subscriptions
  - Built-in authentication
  - File storage cho invoices
- **Connection Pooling**: Optimize database connections
- **Migrations**: Database schema versioning

### 3. AI và Machine Learning
- **Google Gemini 2.5**: Primary AI model cho:
  - OCR (Optical Character Recognition)
  - Natural Language Processing
  - Expense categorization
- **LangChain**: Framework cho building LLM applications
- **LangGraph**: State machine cho complex AI workflows
- **Vector Embeddings**: Semantic search capabilities

### 4. Authentication và Security
- **JWT (JSON Web Tokens)**: Stateless authentication
- **bcrypt**: Password hashing
- **CORS**: Cross-origin resource sharing
- **Input validation**: Pydantic models
- **SQL Injection prevention**: ORM usage

### 5. Backend Dependencies Structure
```python
# Core Framework
fastapi>=0.100.0
uvicorn>=0.23.0
pydantic>=2.0

# AI/ML
langchain>=0.0.300
langgraph>=0.0.10
google-generativeai>=0.3.0

# Database
supabase>=1.0.4
sqlalchemy (implicit via models)

# Security
bcrypt>=4.0.1
PyJWT>=2.8.0
```

## HỆ THỐNG AI VÀ WORKFLOW

### 1. LangGraph State Machine
```python
class AgentState(TypedDict):
    messages: List[BaseMessage]
    user_id: str
    session_id: str
    extracted_expense: Dict
    saved_expense: Dict
    asking_confirmation: bool
    awaiting_user_response: bool
    budget_warning: Dict
    financial_advice: Dict
```

### 2. AI Workflow Nodes
1. **Expense Extraction**: Trích xuất thông tin từ text/image
2. **Confirmation Flow**: Xác nhận với người dùng
3. **Intent Detection**: Phân tích ý định người dùng
4. **Update Processing**: Xử lý chỉnh sửa
5. **Budget Check**: Kiểm tra ngân sách
6. **Financial Advice**: Tư vấn tài chính

### 3. OCR Processing Pipeline
```python
def process_invoice(image_data):
    # 1. Image preprocessing
    image = Image.open(image_data)
    
    # 2. AI-powered extraction
    response = gemini_model.generate_content([prompt, image])
    
    # 3. JSON parsing and validation
    extracted_data = json.loads(response.text)
    
    # 4. Return structured data
    return {
        "store_name": extracted_data.get("store_name"),
        "date": extracted_data.get("date"),
        "total_amount": extracted_data.get("total_amount")
    }
```

## CÔNG NGHỤ PHÁT TRIỂN VÀ DEPLOYMENT

### 1. Development Tools
- **Code Quality**:
  - Black: Code formatting
  - Ruff: Linting và import sorting
  - MyPy: Static type checking
- **Testing**:
  - Pytest: Unit và integration testing
  - Pytest-asyncio: Async test support
  - Test coverage reporting

### 2. Containerization
- **Docker**: Container hóa ứng dụng
- **Docker Compose**: Multi-container orchestration
- **Multi-stage builds**: Optimize image sizes

### 3. Environment Configuration
```python
# Backend Configuration
DATABASE_URL = os.getenv("DATABASE_URL")
SUPABASE_URL = os.getenv("SUPABASE_URL")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")

# Frontend Configuration
NEXT_PUBLIC_API_URL = process.env.NEXT_PUBLIC_API_URL
NEXT_PUBLIC_SUPABASE_URL = process.env.NEXT_PUBLIC_SUPABASE_URL
```

## DATA MODELS VÀ SCHEMA

### 1. Core Models
- **User**: Thông tin người dùng
- **Expense**: Giao dịch chi tiêu
- **Category**: Danh mục chi tiêu
- **Budget**: Ngân sách theo danh mục
- **Invoice**: Hóa đơn uploaded
- **AIInteraction**: Lịch sử tương tác AI

### 2. API Schema Design
```python
# Pydantic schemas cho API
class ExpenseCreate(BaseModel):
    amount: float
    merchant_name: str
    category_id: Optional[str]
    date: datetime
    
class ExpenseResponse(BaseModel):
    id: str
    amount: float
    merchant_name: str
    category: CategoryResponse
    date: datetime
    created_at: datetime
```

## PERFORMANCE VÀ OPTIMIZATION

### 1. Backend Optimization
- **Database Connection Pooling**: Reuse connections
- **Async/Await**: Non-blocking I/O operations
- **Caching**: Redis cho frequently accessed data
- **Lazy Loading**: AI model initialization

### 2. Frontend Optimization
- **Code Splitting**: Dynamic imports
- **Image Optimization**: Next.js Image component
- **Bundle Analysis**: Package size optimization
- **Memoization**: React.memo và useMemo

### 3. AI Model Optimization
- **Model Selection**: Gemini 2.5-flash cho speed
- **Prompt Engineering**: Optimized prompts
- **Batch Processing**: Multiple invoices processing
- **Response Caching**: Cache OCR results

## SECURITY VÀ COMPLIANCE

### 1. Data Protection
- **Encryption**: Data at rest và in transit
- **PII Redaction**: Remove sensitive information
- **Access Control**: Role-based permissions
- **Audit Logging**: Track data access

### 2. API Security
- **Rate Limiting**: Prevent abuse
- **Input Validation**: Pydantic models
- **CORS Configuration**: Restrict origins
- **JWT Expiration**: Token lifecycle management

## MONITORING VÀ OBSERVABILITY

### 1. Application Monitoring
- **Structured Logging**: JSON format logs
- **Error Tracking**: Exception handling
- **Performance Metrics**: Response times
- **Health Checks**: Service availability

### 2. AI Model Monitoring
- **Accuracy Metrics**: OCR extraction quality
- **Latency Tracking**: AI response times
- **Usage Analytics**: Feature utilization
- **Model Performance**: Continuous evaluation

## SCALABILITY VÀ FUTURE ENHANCEMENTS

### 1. Horizontal Scaling
- **Load Balancing**: Multiple backend instances
- **Database Sharding**: Partition user data
- **CDN Integration**: Static asset delivery
- **Microservice Decomposition**: Further service splitting

### 2. AI Enhancement Roadmap
- **Custom Model Training**: Domain-specific models
- **Multi-language Support**: Expand beyond Vietnamese
- **Advanced Analytics**: Predictive insights
- **Voice Input**: Speech-to-text integration

### 3. Feature Expansion
- **Investment Tracking**: Portfolio management
- **Bill Reminders**: Automated notifications
- **Family Accounts**: Shared expense tracking
- **Third-party Integrations**: Bank API connections

## KẾT LUẬN

Moniagent sử dụng stack công nghệ hiện đại với:
- **Frontend**: Next.js 15 + React 18 + TypeScript
- **Backend**: FastAPI + Python 3.10 + Supabase
- **AI**: Google Gemini 2.5 + LangChain + LangGraph
- **DevOps**: Docker + Modern testing tools

Kiến trúc này đảm bảo tính scalable, maintainable, và extensible cho việc phát triển các tính năng AI phức tạp trong tương lai.