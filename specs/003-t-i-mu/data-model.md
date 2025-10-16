# Data Model: Chat Interface with AI Agent for Expense Tracking

## Entity: Expense
**Description**: Represents a single expense transaction with price, location/restaurant, date, and category

**Fields**:
- id: UUID (Primary Key)
- user_id: UUID (Foreign Key to User)
- amount: Decimal (Positive monetary value)
- merchant_name: String (Name of location/restaurant where expense occurred)
- expense_date: Date (Date of the expense, optional)
- category_id: UUID (Foreign Key to Expense Category)
- created_at: DateTime (Timestamp of record creation)
- updated_at: DateTime (Timestamp of last update)
- confirmed_by_user: Boolean (Whether the user confirmed the extracted information)
- source_type: Enum (Values: "image", "text", indicating how the expense was input)
- source_metadata: JSON (Additional information about the source, like image filename)

**Validation Rules**:
- amount must be positive
- expense_date cannot be in the future
- user_id must reference a valid user
- category_id must reference a valid expense category
- confirmed_by_user defaults to false until user confirms

## Entity: User Budget
**Description**: Represents monthly spending limits for different expense categories

**Fields**:
- id: UUID (Primary Key)
- user_id: UUID (Foreign Key to User)
- category_id: UUID (Foreign Key to Expense Category)
- budget_limit: Decimal (Maximum monthly budget for this category)
- month: Integer (1-12, month of the budget)
- year: Integer (Year of the budget)
- created_at: DateTime (Timestamp of record creation)
- updated_at: DateTime (Timestamp of last update)

**Validation Rules**:
- budget_limit must be positive
- month must be between 1-12
- year must be a reasonable value (not in distant past or future)
- user_id must reference a valid user
- category_id must reference a valid expense category
- (user_id, category_id, month, year) combination must be unique

## Entity: Chat Session
**Description**: Represents the interaction history between user and AI agent

**Fields**:
- id: UUID (Primary Key)
- user_id: UUID (Foreign Key to User)
- session_title: String (Generated title for the session)
- created_at: DateTime (Timestamp of session creation)
- updated_at: DateTime (Timestamp of last interaction)
- status: Enum (Values: "active", "completed", "archived")

**Validation Rules**:
- user_id must reference a valid user
- status must be one of the allowed values

## Entity: Expense Category
**Description**: Represents types of expenses (e.g., dining, transportation, groceries)

**Fields**:
- id: UUID (Primary Key)
- name: String (Name of the expense category)
- description: String (Optional description of the category)
- icon: String (Optional icon identifier for UI)
- created_at: DateTime (Timestamp of record creation)
- updated_at: DateTime (Timestamp of last update)
- user_id: UUID (Optional Foreign Key to User - null for system default categories)

**Validation Rules**:
- name must be unique for a given user_id (users can customize categories but not have duplicates)
- name is required and cannot be empty
- if user_id is null, this is a system default category

## Relationships:
- One User can have many Expenses
- One Expense belongs to one Expense Category
- One User can have many User Budgets
- One User Budget belongs to one Expense Category
- One User can have many Chat Sessions
- One Expense has one User (who created it)
- One Chat Session has one User
- One User Budget has one User
- One Expense Category can have many Users (if system default) or one specific User (if custom)

## State Transitions:
### Expense:
- New expense created -> confirmed_by_user = false
- User confirms extracted information -> confirmed_by_user = true
- User rejects and corrects information -> confirmed_by_user = false (until reconfirmed)

### Chat Session:
- New session started -> status = "active"
- Session completed -> status = "completed"
- Session archived -> status = "archived"