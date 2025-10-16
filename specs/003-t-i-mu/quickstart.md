# Quickstart Guide: Chat Interface with AI Agent for Expense Tracking

## Prerequisites

- Python 3.12.6
- pip package manager
- Git
- Access to Google AI SDK (gemini-2.5-flash-lite, gemini-2.5-flash)
- Supabase account and credentials

## Setup Instructions

### 1. Clone the Repository
```bash
git clone <repository-url>
cd <repository-name>
```

### 2. Create and Activate Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Environment Configuration
Create a `.env` file in the project root with the following variables:

```env
GOOGLE_AI_API_KEY=your_google_ai_api_key
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_service_role_key
```

### 5. Database Setup
Run database migrations to create the required tables:

```bash
# Example command - implementation may vary based on your DB setup
python -m src.database.migrate
```

## Running the Application

### Start the Backend Server
```bash
cd backend
python -m src.main
```

The API will be accessible at `http://localhost:8000`

## Key Endpoints

### Chat Interface
- `POST /chat/start` - Start a new chat session
- `POST /chat/{sessionId}/message` - Send a message to the AI agent (text or image)

### Expense Management
- `POST /expenses` - Create an expense record
- `PUT /expenses/{expenseId}` - Update an expense record

### Budget Management
- `POST /budgets/warnings` - Check budget status and get warnings

## Testing

Run the test suite:

```bash
cd backend
pytest
```

To run specific tests:
```bash
# Unit tests
pytest tests/unit/

# Integration tests
pytest tests/integration/

# Contract tests
pytest tests/contract/
```

## Development Guidelines

1. **TDD Approach**: Write tests before implementing features
2. **Code Quality**: Follow the project's code quality standards
3. **Documentation**: Update documentation with new features
4. **Security**: Follow secure coding practices
5. **Performance**: Consider performance implications of your changes

## Key Components

1. **AI Agent Service**: Handles communication with Google AI models
2. **OCR Service**: Processes images to extract text information
3. **Expense Processing Service**: Manages the workflow for extracting and validating expense information
4. **Budget Warning Service**: Calculates current spending and budget limits
5. **API Routes**: Expose endpoints for the frontend to interact with

## Project Structure
```
backend/
├── src/
│   ├── models/          # Data models (Expense, UserBudget, etc.)
│   ├── services/        # Business logic services
│   ├── api/             # API route definitions
│   └── utils/           # Utility functions
└── tests/
    ├── contract/        # API contract tests
    ├── integration/     # Integration tests
    └── unit/            # Unit tests
```