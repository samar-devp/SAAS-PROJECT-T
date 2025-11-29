# Expense Management Module

## Overview
Advanced expense management system designed for Indian businesses with comprehensive tax compliance (GST, TDS), approval workflows, reimbursement processing, and budget tracking.

## Features

### 1. Expense Categories
- Create and manage expense categories
- Configure GST rates per category
- Configure TDS rates per category
- Set approval requirements
- Set receipt requirements
- Configure spending limits (per transaction, per month)
- Monthly budget allocation

### 2. Expense Submission
- Submit expenses with receipts
- Automatic GST/TDS calculation
- Support for multiple payment modes (Cash, Card, UPI, NEFT, RTGS, etc.)
- Vendor information (GSTIN, Invoice details)
- Location tracking
- Travel expense tracking (mileage, distance)
- Project/Task association
- Tagging system

### 3. Approval Workflow
- Multi-level approval support
- Configurable approval rules based on amount
- Auto-approval for expenses below threshold
- Manager approval for higher amounts
- Finance approval for very high amounts
- Rejection with reason tracking

### 4. Reimbursement
- Batch reimbursement processing
- Multiple expense grouping
- Reimbursement cycles (Weekly, Bi-weekly, Monthly)
- Payment tracking
- Payroll integration
- Payment reference tracking

### 5. Budget Management
- Monthly/Yearly budget allocation
- Category-wise budgets
- Budget utilization tracking
- Alert thresholds
- Budget vs Actual reports

### 6. Reports & Analytics
- Expense dashboard with key metrics
- Category-wise expense breakdown
- Employee-wise expense reports
- Status-wise reports
- Date range filtering
- Excel export

## API Endpoints

### Expense Categories
```
GET    /api/expense-categories/<admin_id>              - List all categories
POST   /api/expense-categories/<admin_id>              - Create category
GET    /api/expense-categories/<admin_id>/<pk>         - Get category details
PUT    /api/expense-categories/<admin_id>/<pk>         - Update category
DELETE /api/expense-categories/<admin_id>/<pk>         - Delete category
```

### Expenses
```
GET    /api/expenses/<admin_id>                        - List expenses (with filters)
POST   /api/expenses/<admin_id>                        - Create expense
GET    /api/expenses/<admin_id>/<pk>                   - Get expense details
PUT    /api/expenses/<admin_id>/<pk>                   - Update expense
```

**Query Parameters:**
- `status` - Filter by status (draft, submitted, pending, approved, rejected, reimbursed)
- `employee_id` - Filter by employee
- `category_id` - Filter by category
- `date_from` - Start date
- `date_to` - End date

### Expense Approval
```
POST   /api/expense-approval/<expense_id>              - Approve/Reject expense
```

**Request Body:**
```json
{
  "action": "approve",  // or "reject"
  "comments": "Approved as per policy"
}
```

### Reimbursement
```
POST   /api/expense-reimbursement/<admin_id>           - Create reimbursement
```

**Request Body:**
```json
{
  "employee_id": "uuid",
  "expense_ids": ["uuid1", "uuid2"],
  "reimbursement_date": "2024-01-15"
}
```

### Budget
```
GET    /api/expense-budget/<admin_id>                  - List budgets
POST   /api/expense-budget/<admin_id>                  - Create budget
```

**Query Parameters:**
- `year` - Budget year
- `month` - Budget month (optional)

### Dashboard
```
GET    /api/expense-dashboard/<admin_id>               - Get dashboard stats
```

**Query Parameters:**
- `date_from` - Start date
- `date_to` - End date

## Models

### ExpenseCategory
- `name` - Category name
- `code` - Category code
- `gst_applicable` - Whether GST is applicable
- `gst_rate` - GST percentage
- `tds_applicable` - Whether TDS is applicable
- `tds_rate` - TDS percentage
- `max_amount_per_transaction` - Maximum amount per transaction
- `max_amount_per_month` - Maximum amount per month
- `requires_approval` - Whether approval is required
- `requires_receipt` - Whether receipt is required
- `monthly_budget` - Monthly budget allocation

### Expense
- `title` - Expense title
- `description` - Expense description
- `expense_date` - Date of expense
- `amount` - Base amount
- `gst_amount` - GST amount
- `tds_amount` - TDS amount
- `total_amount` - Total amount after tax
- `payment_mode` - Payment mode
- `vendor_name` - Vendor name
- `vendor_gstin` - Vendor GSTIN
- `invoice_number` - Invoice number
- `status` - Expense status
- `receipts` - Receipt file paths (JSON array)
- `is_travel_expense` - Whether it's a travel expense
- `distance_km` - Distance in kilometers
- `rate_per_km` - Rate per kilometer

### ExpensePolicy
- `name` - Policy name
- `effective_from` - Effective from date
- `max_expense_per_day` - Maximum expense per day
- `max_expense_per_month` - Maximum expense per month
- `auto_approve_below` - Auto-approve below this amount
- `requires_manager_approval_above` - Manager approval required above this amount
- `requires_finance_approval_above` - Finance approval required above this amount
- `submission_deadline_days` - Days after expense date to submit
- `reimbursement_cycle` - Reimbursement cycle (weekly, biweekly, monthly)

### ExpenseBudget
- `category` - Expense category
- `year` - Budget year
- `month` - Budget month (optional)
- `allocated_budget` - Allocated budget amount
- `spent_amount` - Spent amount
- `pending_amount` - Pending amount
- `alert_threshold_percentage` - Alert threshold percentage

## Tax Calculations

### GST Calculation
If GST is applicable:
```
GST Amount = (Amount × GST Rate) / 100
Amount Before Tax = Amount / (1 + GST Rate / 100)
```

### TDS Calculation
If TDS is applicable:
```
TDS Amount = (Amount × TDS Rate) / 100
Total Amount = Amount - TDS Amount
```

## Celery Tasks

### process_expense_reimbursements_task
- Runs weekly (Every Monday at 9 AM)
- Processes pending expense reimbursements
- Updates reimbursement status
- Integrates with payroll system

## Usage Examples

### Create Expense Category
```python
POST /api/expense-categories/<admin_id>
{
  "name": "Travel",
  "code": "TRAVEL",
  "gst_applicable": true,
  "gst_rate": 18.00,
  "tds_applicable": false,
  "requires_approval": true,
  "requires_receipt": true,
  "max_amount_per_transaction": 10000.00,
  "monthly_budget": 50000.00
}
```

### Submit Expense
```python
POST /api/expenses/<admin_id>
{
  "employee": "employee_uuid",
  "category": "category_id",
  "title": "Taxi fare to client meeting",
  "description": "Travel to client office",
  "expense_date": "2024-01-15",
  "amount": 500.00,
  "payment_mode": "cash",
  "location": "Mumbai",
  "city": "Mumbai",
  "state": "Maharashtra",
  "is_travel_expense": true,
  "distance_km": 25.5,
  "rate_per_km": 12.00,
  "receipts": ["/media/receipts/receipt1.jpg"]
}
```

### Approve Expense
```python
POST /api/expense-approval/<expense_id>
{
  "action": "approve",
  "comments": "Approved as per travel policy"
}
```

## Best Practices

1. **Category Setup**: Create comprehensive categories covering all expense types
2. **Policy Configuration**: Set appropriate approval thresholds based on organization hierarchy
3. **Budget Planning**: Allocate realistic budgets per category
4. **Receipt Management**: Always require receipts for expenses above threshold
5. **Regular Reviews**: Review expense reports regularly to identify patterns
6. **Tax Compliance**: Ensure GST/TDS rates are updated as per latest regulations

## Future Enhancements

- OCR for receipt scanning
- Mobile app integration
- Integration with accounting software
- Advanced analytics and forecasting
- Multi-currency support
- Expense policy automation
- AI-powered expense categorization

