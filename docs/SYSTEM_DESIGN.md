# Backend System Design

## Overview

Moniagent backend is a FastAPI-based microservice that provides financial management capabilities with AI-powered expense tracking, OCR processing, and intelligent categorization. The system is designed to handle Vietnamese financial data with natural language processing capabilities.

## Architecture

### Core Components

#### 1. API Layer (`src/api/`)
- **FastAPI Application**: Main application with middleware for CORS, security headers, and exception handling
- **Versioned APIs**: v1 endpoints organized by domain (auth, expenses, categories, budgets, chat)
- **Request Validation**: Pydantic schemas for type-safe request/response handling
- **Error Handling**: Centralized exception handlers with structured error responses

#### 2. Core Services (`src/core/`)
- **Configuration Management**: Environment-based settings with dataclass configuration
- **Database Integration**: Dual database approach with Supabase (PostgreSQL) and SQLAlchemy
- **Security**: JWT-based authentication with secure token management
- **AI Configuration**: Google Gemini AI integration for OCR and text processing
- **LangGraph Agent**: Sophisticated workflow engine for AI-powered conversations

#### 3. Business Logic (`src/services/`)
- **Expense Processing**: OCR extraction, validation, and storage
- **AI Agent Service**: Conversational AI with confirmation flows
- **Budget Management**: Budget tracking and warning system
- **Categorization**: ML-based expense categorization with learning
- **Financial Advice**: AI-powered spending insights and recommendations

#### 4. Data Models (`src/models/`)
- **SQLAlchemy ORM**: Database models with relationships
- **User Management**: User profiles and preferences
- **Expense Tracking**: Expenses, invoices, and categorization
- **Budget System**: Budget definitions and tracking
- **AI Interaction**: Chat sessions and learning data

## Key Features

### 1. AI-Powered Expense Processing
- **OCR Integration**: Google Gemini 2.5 for invoice image processing
- **Natural Language Extraction**: Text-based expense entry with Vietnamese support
- **Intelligent Categorization**: ML models that learn from user corrections
- **Confirmation Flow**: Interactive confirmation before saving expenses

### 2. Conversational AI Agent
- **LangGraph Workflow**: State-based conversation management
- **Multi-turn Dialogues**: Support for corrections and updates
- **Intent Recognition**: Distinguishes between expense reporting and advice requests
- **Vietnamese NLP**: Native language support for financial conversations

### 3. Budget Management
- **Real-time Tracking**: Budget vs. actual spending monitoring
- **Warning System**: Automated alerts when approaching limits
- **Category-based Budgets**: Fine-grained budget control by expense category
- **Period Management**: Daily, weekly, monthly budget cycles

### 4. Learning System
- **Category Learning**: Improves categorization accuracy from user feedback
- **User Personalization**: Adapts to individual spending patterns
- **Feedback Loop**: Continuous improvement through corrections
- **Keyword Extraction**: Learns merchant and category associations

## Database Architecture

### Dual Database Approach
1. **Supabase (PostgreSQL)**: Primary data store for user data, expenses, budgets
2. **SQLAlchemy ORM**: Local development and testing with SQLite fallback

### Key Tables
- `users`: User profiles and authentication
- `expenses`: Expense records with categorization
- `categories`: User-defined expense categories
- `budgets`: Budget definitions and tracking
- `ai_interactions`: Chat sessions and AI responses
- `categorization_feedback`: Learning data for improvement

## Security Architecture

### Authentication & Authorization
- **JWT Tokens**: Secure token-based authentication
- **Role-based Access**: User-scoped data access
- **Session Management**: Secure session handling with expiration

### Data Protection
- **Input Validation**: Comprehensive request validation
- **SQL Injection Prevention**: ORM-based database access
- **CORS Configuration**: Restricted cross-origin access
- **Security Headers**: XSS protection, content type validation

## AI/ML Integration

### Google Gemini AI
- **OCR Processing**: Invoice image to text conversion
- **Text Extraction**: Structured data extraction from unstructured text
- **Natural Language Understanding**: Vietnamese language processing

### LangGraph Workflow Engine
- **State Management**: Conversation state persistence
- **Conditional Routing**: Dynamic conversation flows
- **Interrupt Handling**: User interaction pauses
- **Error Recovery**: Graceful handling of AI failures

## API Design

### RESTful Principles
- **Resource-based URLs**: Clear resource hierarchy
- **HTTP Methods**: Proper use of GET, POST, PUT, DELETE
- **Status Codes**: Consistent HTTP status code usage
- **Versioning**: API versioning for backward compatibility

### Key Endpoints
- `/auth/v1/`: Authentication and user management
- `/expenses/v1/`: Expense CRUD operations
- `/categories/v1/`: Category management
- `/budgets/v1/`: Budget operations
- `/chat/v1/`: AI agent interactions
- `/invoices/v1/`: Invoice processing and OCR

## Performance Considerations

### Caching Strategy
- **In-memory Caching**: Frequently accessed data
- **Database Connection Pooling**: Efficient database connections
- **AI Response Caching**: Cache repeated AI queries

### Scalability
- **Async Operations**: Non-blocking I/O for better performance
- **Database Optimization**: Indexed queries and efficient joins
- **Microservice Ready**: Clean separation of concerns

## Development Workflow

### Code Organization
- **Domain-driven Design**: Clear separation of business domains
- **Dependency Injection**: Clean dependency management
- **Service Layer Pattern**: Business logic abstraction
- **Repository Pattern**: Data access abstraction

### Testing Strategy
- **Unit Tests**: Individual component testing
- **Integration Tests**: Service interaction testing
- **Contract Tests**: API contract validation
- **Security Tests**: Vulnerability scanning

## Deployment Architecture

### Containerization
- **Docker Support**: Containerized deployment
- **Environment Configuration**: Flexible environment management
- **Health Checks**: Application health monitoring

### Monitoring & Logging
- **Structured Logging**: JSON-formatted logs for analysis
- **Error Tracking**: Comprehensive error reporting
- **Performance Metrics**: Application performance monitoring

## Technology Stack

### Core Technologies
- **FastAPI**: Modern Python web framework
- **SQLAlchemy**: Python SQL toolkit and ORM
- **Supabase**: Backend-as-a-Service with PostgreSQL
- **Pydantic**: Data validation using Python type annotations

### AI/ML Technologies
- **Google Gemini AI**: OCR and text processing
- **LangChain**: LLM application framework
- **LangGraph**: Stateful AI workflow management

### Development Tools
- **Black**: Code formatting
- **Ruff**: Linting and code analysis
- **MyPy**: Static type checking
- **Pytest**: Testing framework

## Future Enhancements

### Scalability
- **Microservices**: Split into specialized services
- **Message Queues**: Asynchronous task processing
- **Load Balancing**: Horizontal scaling capabilities

### AI Improvements
- **Custom Models**: Domain-specific fine-tuning
- **Real-time Learning**: Online learning capabilities
- **Advanced Analytics**: Predictive spending insights

### Integration
- **Bank APIs**: Direct bank integration
- **Payment Systems**: Payment gateway integration
- **Third-party Services**: External financial data sources