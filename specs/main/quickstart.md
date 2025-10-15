# Quickstart Guide for Frontend Developers

## Overview
This guide helps frontend developers integrate with the Financial Assistant backend API. The backend provides services for user authentication, invoice OCR processing, expense management, categorization, and AI-powered financial advice.

## Base API URL
```
https://api.moniagent.com/v1
```

## Authentication
All API endpoints (except authentication) require a JWT token in the Authorization header:

```
Authorization: Bearer <your-jwt-token>
```

## Getting Started Steps

### 1. User Registration
First, register a new user account:

```javascript
fetch('https://api.moniagent.com/v1/auth/register', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    email: 'user@example.com',
    password: 'securePassword123',
    first_name: 'John',
    last_name: 'Doe'
  })
})
.then(response => response.json())
.then(data => console.log(data));
```

### 2. User Login
Authenticate to get a JWT token:

```javascript
fetch('https://api.moniagent.com/v1/auth/login', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    email: 'user@example.com',
    password: 'securePassword123'
  })
})
.then(response => response.json())
.then(data => {
  // Store the access token for subsequent requests
  localStorage.setItem('token', data.access_token);
});
```

### 3. Invoice Processing
Upload and process an invoice for OCR:

```javascript
const formData = new FormData();
formData.append('file', invoiceImageFile);

fetch('https://api.moniagent.com/v1/invoices', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${localStorage.getItem('token')}`
  },
  body: formData
})
.then(response => response.json())
.then(data => console.log(data));
```

### 4. Expense Management
Retrieve and manage expenses:

```javascript
// Get user expenses
fetch('https://api.moniagent.com/v1/expenses', {
  headers: {
    'Authorization': `Bearer ${localStorage.getItem('token')}`
  }
})
.then(response => response.json())
.then(data => console.log(data.items));

// Create a manual expense
fetch('https://api.moniagent.com/v1/expenses', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${localStorage.getItem('token')}`
  },
  body: JSON.stringify({
    amount: 25.50,
    date: '2025-10-15',
    category_id: 'uuid-string',
    description: 'Lunch at restaurant'
  })
})
.then(response => response.json())
.then(data => console.log(data));
```

## Key API Endpoints for Frontend

### Authentication
- `POST /auth/register` - Create new account
- `POST /auth/login` - Get JWT token

### Invoice Processing (OCR)
- `POST /invoices` - Upload and process invoice image
- `GET /invoices/{id}` - Get specific invoice details
- `PUT /invoices/{id}` - Update invoice details after user review

### Expense Management
- `GET /expenses` - List user expenses with filters
- `POST /expenses` - Create manual expense
- `GET /expenses/{id}` - Get specific expense
- `PUT /expenses/{id}` - Update expense details
- `DELETE /expenses/{id}` - Remove expense

### Categories
- `GET /categories` - List available categories
- `POST /categories` - Create custom category

### Budget Management
- `GET /budgets` - List user budgets
- `POST /budgets` - Create new budget

### AI Agent Features
- `POST /ai-agent/categorize-expense` - Get AI category suggestion
- `GET /ai-agent/financial-advice` - Get AI financial advice

## Error Handling
The API returns appropriate HTTP status codes:
- `200-201`: Success
- `400`: Bad request (validation error)
- `401`: Unauthorized (missing or invalid token)
- `404`: Resource not found
- `409`: Conflict (e.g., email already exists)
- `500`: Server error

## Best Practices for Frontend Integration

1. **Token Management**: Store JWT tokens securely (preferably in httpOnly cookies or secure local storage)
2. **File Uploads**: For invoice processing, use FormData for image uploads
3. **Error Messages**: Present user-friendly error messages from API responses
4. **Loading States**: Show loading indicators during longer operations like OCR processing
5. **Form Validation**: Validate user inputs before sending to API

## Example: Complete Invoice Processing Workflow

```javascript
// Step 1: Upload invoice
async function processInvoice(file) {
  const token = localStorage.getItem('token');
  const formData = new FormData();
  formData.append('file', file);

  try {
    const response = await fetch('https://api.moniagent.com/v1/invoices', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`
      },
      body: formData
    });

    if (response.ok) {
      const invoice = await response.json();
      // Show extracted data to user for confirmation
      displayInvoiceData(invoice);
      return invoice;
    } else {
      throw new Error('Failed to process invoice');
    }
  } catch (error) {
    console.error('Error processing invoice:', error);
  }
}

// Step 2: Allow user to review and edit extracted data
function displayInvoiceData(invoice) {
  document.getElementById('store-name').value = invoice.store_name;
  document.getElementById('invoice-date').value = invoice.date;
  document.getElementById('total-amount').value = invoice.total_amount;
}

// Step 3: Update invoice after user review
async function updateInvoice(invoiceId, updatedData) {
  const token = localStorage.getItem('token');

  const response = await fetch(`https://api.moniagent.com/v1/invoices/${invoiceId}`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify(updatedData)
  });

  return response.json();
}
```

## Support and Documentation
- API documentation is automatically available at `/docs` and `/redoc` endpoints
- For questions, contact the backend team or refer to the full API specification