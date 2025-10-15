# Data Model for Financial Assistant with OCR and Expense Management

## Entity: User
Represents a financial assistant account

**Fields:**
- `id` (UUID): Unique identifier for the user
- `email` (string): User's email address (unique, required)
- `password_hash` (string): Hashed password for authentication
- `first_name` (string): User's first name
- `last_name` (string): User's last name
- `created_at` (datetime): Account creation timestamp
- `updated_at` (datetime): Last update timestamp
- `budget_preferences` (jsonb): User's budget settings and preferences
- `notification_preferences` (jsonb): User's notification settings

**Validation rules:**
- Email must be valid and unique
- Password must meet complexity requirements
- First name and last name are optional but must be reasonable length

## Entity: Invoice
Digital representation of the original receipt/image with extracted text and metadata

**Fields:**
- `id` (UUID): Unique identifier for the invoice
- `user_id` (UUID): Foreign key to User
- `image_url` (string): URL to the stored invoice image
- `original_text` (text): Raw text extracted from the image
- `store_name` (string): Name of the store/vendor from the invoice
- `date` (date): Date of the transaction from the invoice
- `total_amount` (decimal): Total amount from the invoice
- `extracted_at` (datetime): When OCR extraction was performed
- `status` (string): Status of processing (pending, processed, failed)
- `confidence_score` (float): AI confidence in the extracted data
- `raw_ocr_data` (jsonb): Raw OCR response data for debugging

**Relationships:**
- Belongs to one User
- Has one Expense (after processing)

**Validation rules:**
- All extracted fields must be present after processing
- Amount must be a positive decimal
- Date must be within reasonable range
- Status must be one of the allowed values

## Entity: Expense
Represents a single financial transaction with attributes: store name, date, amount, category, image reference, user confirmation status

**Fields:**
- `id` (UUID): Unique identifier for the expense
- `user_id` (UUID): Foreign key to User
- `invoice_id` (UUID): Foreign key to Invoice (optional if manually entered)
- `store_name` (string): Name of the store/vendor
- `date` (date): Date of the transaction
- `amount` (decimal): Amount of the expense
- `category_id` (UUID): Foreign key to Category
- `description` (string): Additional description of the expense (optional)
- `user_confirmed` (boolean): Whether user has confirmed the expense details
- `categorized_by_ai` (boolean): Whether the category was assigned by AI
- `created_at` (datetime): When the expense was created
- `updated_at` (datetime): Last update timestamp

**Relationships:**
- Belongs to one User
- Belongs to one Invoice (optional)
- Belongs to one Category

**Validation rules:**
- Amount must be positive
- Date must be valid
- Must be associated with either an invoice or have manually entered data
- Category must be valid

## Entity: Category
Predefined expense classification (e.g., "Eating Out", "Transportation", "Shopping", "Utilities") with budget limits and historical spending patterns

**Fields:**
- `id` (UUID): Unique identifier for the category
- `name` (string): Name of the category (e.g., "Eating Out")
- `description` (string): Description of the category
- `color` (string): Color code for UI representation
- `icon` (string): Icon identifier for UI representation
- `user_id` (UUID): Foreign key to User (null for system categories)
- `is_system_category` (boolean): Whether this is a built-in category
- `monthly_budget_limit` (decimal): Monthly budget limit for this category (optional)
- `created_at` (datetime): When the category was created
- `updated_at` (datetime): Last update timestamp

**Relationships:**
- Belongs to one User (or system if is_system_category is true)
- Has many Expenses

**Validation rules:**
- Name must be unique per user
- Budget limit must be positive if provided
- Color must be valid hex code if provided

## Entity: Budget
User-defined spending limit per category per time period with alert thresholds

**Fields:**
- `id` (UUID): Unique identifier for the budget
- `user_id` (UUID): Foreign key to User
- `category_id` (UUID): Foreign key to Category
- `time_period` (string): Time period for budget (weekly, monthly, annually)
- `budget_amount` (decimal): Amount allocated for this budget
- `alert_threshold_percentage` (integer): Percentage of budget that triggers alert (default: 80)
- `current_spending` (decimal): Current spending in this budget period (calculated)
- `start_date` (date): Start date of the budget period
- `end_date` (date): End date of the budget period
- `created_at` (datetime): When the budget was created
- `updated_at` (datetime): Last update timestamp

**Relationships:**
- Belongs to one User
- Belongs to one Category

**Validation rules:**
- Budget amount must be positive
- Time period must be one of the allowed values
- Threshold percentage must be between 0 and 100
- Start date must be before end date

## Entity: ExpenseCategorizationRule
Stores user-specific categorization preferences to improve AI suggestions

**Fields:**
- `id` (UUID): Unique identifier for the rule
- `user_id` (UUID): Foreign key to User
- `store_name_pattern` (string): Pattern to match store names (e.g., "Highlands Coffee", "Grab")
- `suggested_category_id` (UUID): Category ID that should be suggested for this pattern
- `usage_count` (integer): How many times this rule has been applied
- `created_at` (datetime): When the rule was created
- `updated_at` (datetime): Last update timestamp

**Relationships:**
- Belongs to one User
- Belongs to one Category

**Validation rules:**
- Store pattern and user combination must be unique
- Category must exist

## Entity: AIInteraction
Tracks AI interactions and user feedback for learning and improvement

**Fields:**
- `id` (UUID): Unique identifier for the interaction
- `user_id` (UUID): Foreign key to User
- `interaction_type` (string): Type of interaction (ocr_process, categorization, financial_advice)
- `input_data` (jsonb): Input data provided to the AI
- `ai_response` (jsonb): Response from the AI
- `user_feedback` (string): Feedback from user about AI response quality
- `created_at` (datetime): When the interaction occurred

**Relationships:**
- Belongs to one User

**Validation rules:**
- Interaction type must be one of the allowed values
- Required fields must be present based on interaction type

## State Transitions

### Invoice State Transitions:
- `pending` → `processed` (after OCR extraction)
- `pending` → `failed` (if OCR extraction fails)
- `processed` → `confirmed` (after user confirms extracted data)

### Expense State Transitions:
- `unconfirmed` → `confirmed` (after user confirms details)
- `confirmed` → `modified` (if user modifies details later)

## Indexes for Performance

- User.email (unique index)
- Invoice.user_id (index)
- Expense.user_id (index)
- Expense.category_id (index)
- Expense.date (index)
- Category.user_id (index)
- Budget.user_id (index)
- Budget.category_id (index)