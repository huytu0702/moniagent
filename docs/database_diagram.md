# Moniagent Database Schema Diagram

## Entity Relationship Diagram

```mermaid
erDiagram
    users {
        uuid id PK
        string email UK
        string first_name
        string last_name
        string password_hash
        text budget_preferences
        text notification_preferences
        datetime created_at
        datetime updated_at
    }

    invoices {
        uuid id PK
        uuid user_id FK
        string filename
        text file_path
        string store_name
        datetime date
        float total_amount
        text extracted_data
        string status
        datetime created_at
        datetime updated_at
    }

    expenses {
        uuid id PK
        uuid user_id FK
        uuid invoice_id FK
        uuid category_id FK
        text description
        string merchant_name
        float amount
        datetime date
        boolean confirmed_by_user
        string source_type
        text source_metadata
        datetime created_at
        datetime updated_at
    }

    categories {
        uuid id PK
        uuid user_id FK
        string name
        text description
        string icon
        string color
        boolean is_system_category
        integer display_order
        datetime created_at
        datetime updated_at
    }

    budgets {
        uuid id PK
        uuid user_id FK
        uuid category_id FK
        float limit_amount
        string period
        float alert_threshold
        datetime created_at
        datetime updated_at
    }

    ai_interactions {
        uuid id PK
        uuid user_id FK
        string session_id
        string interaction_type
        text input_data
        text output_data
        string model_used
        datetime created_at
    }

    chat_sessions {
        uuid id PK
        uuid user_id FK
        string session_title
        enum status
        datetime created_at
        datetime updated_at
    }

    chat_messages {
        uuid id PK
        uuid session_id FK
        string role
        string content
        datetime created_at
    }

    categorization_feedback {
        uuid id PK
        uuid user_id FK
        uuid expense_id FK
        uuid suggested_category_id FK
        uuid confirmed_category_id FK
        float confidence_score
        string feedback_type
        datetime created_at
    }

    expense_categorization_rules {
        uuid id PK
        uuid user_id FK
        uuid category_id FK
        string store_name_pattern
        string rule_type
        float confidence_threshold
        boolean is_active
        datetime created_at
        datetime updated_at
    }

    %% Relationships
    users ||--o{ invoices : "has"
    users ||--o{ expenses : "has"
    users ||--o{ categories : "has"
    users ||--o{ budgets : "has"
    users ||--o{ ai_interactions : "has"
    users ||--o{ chat_sessions : "has"
    users ||--o{ categorization_feedback : "has"
    users ||--o{ expense_categorization_rules : "has"

    invoices ||--o{ expenses : "generates"

    expenses }o--|| categories : "belongs_to"
    expenses ||--o{ categorization_feedback : "receives"

    categories ||--o{ budgets : "limits"
    categories ||--o{ expense_categorization_rules : "defines"
    categories ||--o{ categorization_feedback : "suggested/confirmed"

    chat_sessions ||--o{ chat_messages : "contains"

    categorization_feedback }o--|| categories : "suggested_category"
    categorization_feedback }o--|| categories : "confirmed_category"
```

## Table Descriptions

### Core Tables

#### `users`
Central user table storing authentication and preferences
- **Primary Key**: `id` (UUID)
- **Unique Constraint**: `email`
- **Relationships**: One-to-many with all user-specific data

#### `invoices`
Stores uploaded invoice images and extracted data
- **Status**: pending, processed, failed
- **Links**: Belongs to user, generates expenses

#### `expenses`
Main expense tracking table
- **Source Types**: "image" (from invoice) or "text" (manual entry)
- **Confirmation**: User can confirm AI-extracted information
- **Links**: Belongs to user, category, and optionally invoice

#### `categories`
Expense categorization with system and user-defined categories
- **Types**: System categories (predefined) vs user categories
- **Display**: Ordered by `display_order` with custom icons/colors

### Budget & Rules Tables

#### `budgets`
Budget limits per category per user
- **Periods**: monthly, weekly, yearly
- **Alerts**: Triggers at `alert_threshold` percentage

#### `expense_categorization_rules`
Auto-categorization rules based on merchant patterns
- **Rule Types**: keyword, regex, exact_match
- **Confidence**: Minimum threshold for auto-application

### AI & Chat Tables

#### `ai_interactions`
Logs all AI interactions for debugging and analytics
- **Types**: invoice_processing, categorization, advice
- **Optional**: Can log interactions for unauthenticated users

#### `chat_sessions` & `chat_messages`
Conversational AI chat functionality
- **Session Status**: active, completed, archived
- **Message Roles**: user, assistant

### Learning Tables

#### `categorization_feedback`
Machine learning feedback loop for categorization improvement
- **Feedback Types**: confirmation, correction
- **Dual Category Links**: Tracks both suggested and confirmed categories

## Key Relationships

1. **User-Centric**: All data belongs to a user with cascade delete
2. **Invoice → Expense**: One invoice can generate multiple expenses
3. **Expense → Category**: Many-to-one relationship with optional categorization
4. **Budget → Category**: One budget per category per user
5. **Learning Loop**: Expenses → Feedback → Rules → Categories

## Data Flow

1. **Invoice Upload** → `invoices` table → AI processing → `expenses` table
2. **Expense Categorization** → AI suggestion → User feedback → `categorization_feedback`
3. **Rule Learning** → Feedback patterns → `expense_categorization_rules`
4. **Budget Monitoring** → Expenses vs `budgets` → Alert thresholds
5. **Chat Interactions** → `chat_sessions` → `chat_messages` → `ai_interactions` logging