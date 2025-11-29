# SAAS Project - HR Management System

## Overview
This is a comprehensive HR Management System built with Django REST Framework, designed specifically for Indian businesses. It includes advanced features for attendance, payroll, leave management, expense management, task management, asset management, and more.

## Features

### 1. **Expense Management** (`Expenditure`)
Advanced expense management system with Indian tax compliance:
- Expense categories with GST/TDS configuration
- Expense submission and approval workflow
- Reimbursement processing
- Budget tracking and alerts
- Dashboard with analytics
- Multi-level approval workflows
- Receipt management
- Travel expense tracking

### 2. **Payroll System** (`PayrollSystem`)
Comprehensive Indian payroll system:
- Salary structure management
- Statutory compliance (PF, ESI, Professional Tax, TDS, LWF)
- Payroll generation and processing
- Payslip generation
- Advance salary management
- Bank information management
- Excel export/import
- Custom payroll sheets

### 3. **Leave Management** (`LeaveControl`)
Advanced leave management:
- Multiple leave types
- Leave policies and accrual
- Carry forward and encashment
- Compensatory off
- Leave approval workflows
- Leave calendar
- Leave reports and analytics

### 4. **Visit Management** (`VisitControl`)
Field visit tracking:
- Visit scheduling and assignment
- Location tracking
- Visit templates and checklists
- Expense tracking per visit
- Visit reports and analytics
- Reminders and notifications

### 5. **Task Management** (`TaskControl`)
Project and task management:
- Project creation and management
- Task assignment and tracking
- Subtasks and dependencies
- Time logging
- Recurring tasks
- Comments and attachments
- Task reports

### 6. **Asset Management** (`AssetManagement`)
Asset lifecycle management:
- Asset categories
- Asset tracking
- Maintenance scheduling
- Asset transfers
- Depreciation calculation
- Asset reports

### 7. **Notes Management** (`NotesManagement`)
Document and note management:
- Note categories
- Rich text notes
- Note sharing and collaboration
- Version control
- Note templates
- Reminders

### 8. **Broadcast Management** (`BroadcastManagement`)
Organization-wide announcements:
- Broadcast creation
- Multi-channel delivery (Email, SMS, Push)
- Targeted broadcasting
- Scheduling
- Acknowledgment tracking
- Templates

### 9. **Notification Management** (`NotificationControl`)
Centralized notification system:
- Multi-channel notifications
- Notification preferences
- Templates
- Delivery tracking
- Analytics

### 10. **Attendance Management** (`WorkLog`)
- Check-in/Check-out
- Shift management
- Auto-checkout (Celery tasks)
- Attendance reports
- Excel export

## Celery Tasks

The system uses Celery for background task processing:

### Auto-Checkout Tasks
- **General Auto-Checkout**: Runs every 5 minutes, checks out employees at fixed time
- **Shift-Wise Auto-Checkout**: Runs every 5 minutes, checks out based on shift end time + grace period

### Periodic Tasks
- **Monthly Payroll Processing**: 1st of every month at 2 AM
- **Leave Accrual Processing**: 1st of every month at 3 AM
- **Asset Depreciation Update**: 1st of every month at 4 AM
- **Expense Reimbursement Processing**: Every Monday at 9 AM
- **Scheduled Notifications**: Every minute
- **Scheduled Broadcasts**: Every minute

## Setup Instructions

### Prerequisites
- Python 3.8+
- Django 5.1+
- Redis (for Celery)
- PostgreSQL/SQLite

### Installation

1. **Install Dependencies**
```bash
pip install -r requirements.txt
```

2. **Install Redis**
```bash
# Windows (using Chocolatey)
choco install redis-64

# Linux
sudo apt-get install redis-server

# macOS
brew install redis
```

3. **Database Setup**
```bash
python manage.py makemigrations
python manage.py migrate
```

4. **Create Superuser**
```bash
python manage.py createsuperuser
```

5. **Run Celery Worker**
```bash
celery -A core worker -l info
```

6. **Run Celery Beat (Scheduler)**
```bash
celery -A core beat -l info
```

7. **Run Django Server**
```bash
python manage.py runserver
```

## API Endpoints

### Expense Management
- `GET/POST /api/expense-categories/<admin_id>` - Category CRUD
- `GET/POST /api/expenses/<admin_id>` - Expense CRUD
- `POST /api/expense-approval/<expense_id>` - Approve/Reject expense
- `POST /api/expense-reimbursement/<admin_id>` - Create reimbursement
- `GET/POST /api/expense-budget/<admin_id>` - Budget management
- `GET /api/expense-dashboard/<admin_id>` - Dashboard stats

### Payroll System
- `GET/POST /api/payroll/salary-structure/<org_id>` - Salary structure
- `GET/POST /api/payroll/employee-assigned-structure/<org_id>` - Assign structure
- `POST /api/payroll/generate-payroll/<org_id>` - Generate payroll
- `GET /api/payroll/payroll-monthly-report/<org_id>/<month>/<year>` - Monthly report

### Leave Management
- `GET/POST /api/leave/leave-types/<admin_id>` - Leave types
- `GET/POST /api/leave/leave-applications/<admin_id>` - Leave applications
- `GET/POST /api/leave/leave-policies/<admin_id>` - Leave policies
- `GET /api/leave/leave-reports/<admin_id>` - Leave reports

### Visit Management
- `GET/POST /api/visit/visits/<admin_id>` - Visit assignments
- `GET/POST /api/visit/templates/<admin_id>` - Visit templates
- `GET /api/visit/dashboard/<admin_id>` - Visit dashboard

### Task Management
- `GET/POST /api/tasks/projects/<admin_id>` - Projects
- `GET/POST /api/tasks/tasks/<admin_id>` - Tasks
- `GET /api/tasks/dashboard/<admin_id>` - Task dashboard

### Asset Management
- `GET/POST /api/asset/categories/<admin_id>` - Asset categories
- `GET/POST /api/asset/assets/<admin_id>` - Assets
- `GET /api/asset/dashboard/<admin_id>` - Asset dashboard

### Notes Management
- `GET/POST /api/notes/categories/<admin_id>` - Note categories
- `GET/POST /api/notes/notes/<admin_id>` - Notes
- `GET /api/notes/search/<admin_id>` - Search notes

### Broadcast Management
- `GET/POST /api/broadcast/broadcasts/<admin_id>` - Broadcasts
- `GET/POST /api/broadcast/templates/<admin_id>` - Broadcast templates
- `GET /api/broadcast/analytics/<admin_id>` - Broadcast analytics

### Notification Management
- `GET/POST /api/notification/notifications/<admin_id>` - Notifications
- `GET/POST /api/notification/preferences/<admin_id>` - Notification preferences
- `GET /api/notification/analytics/<admin_id>` - Notification analytics

## Configuration

### Celery Configuration
Update `core/settings.py`:
```python
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
```

### Timezone
Default timezone is set to `Asia/Kolkata` (IST).

## Database Models

### Expense Management
- `ExpenseCategory` - Expense categories with tax settings
- `Expense` - Individual expense records
- `ExpensePolicy` - Organization expense policies
- `ExpenseApprovalWorkflow` - Multi-level approval
- `ExpenseReimbursement` - Reimbursement batches
- `ExpenseBudget` - Budget tracking
- `ExpenseReport` - Expense reports

### Payroll System
- `SalaryComponent` - Salary components
- `SalaryStructure` - Salary structures
- `PayrollRecord` - Monthly payroll records
- `EmployeeBankInfo` - Bank details
- `PayrollSettings` - Organization payroll settings

### Leave Management
- `LeaveType` - Leave types
- `LeavePolicy` - Leave policies
- `LeaveApplication` - Leave applications
- `EmployeeLeaveBalance` - Leave balances
- `CompensatoryOff` - Comp-off management

## Testing

Run tests:
```bash
python manage.py test
```

## Production Deployment

1. Set `DEBUG = False` in settings
2. Configure proper database (PostgreSQL recommended)
3. Set up Redis for Celery
4. Configure static files serving
5. Set up proper logging
6. Use environment variables for sensitive data

## License

Proprietary - All rights reserved

## Support

For support, contact the development team.

