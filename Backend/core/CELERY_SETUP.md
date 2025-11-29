# Celery Setup and Configuration Guide

## Overview
This project uses Celery for asynchronous task processing and scheduled tasks. Celery is configured to work with Redis as the message broker and result backend.

## Prerequisites

1. **Redis Installation**
   - Windows: `choco install redis-64` or download from https://github.com/microsoftarchive/redis/releases
   - Linux: `sudo apt-get install redis-server`
   - macOS: `brew install redis`

2. **Python Packages**
   ```bash
   pip install celery redis
   ```

## Configuration

### Settings (core/settings.py)
```python
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'Asia/Kolkata'
CELERY_ENABLE_UTC = False
```

## Running Celery

### 1. Start Redis Server
```bash
# Windows
redis-server

# Linux/macOS
redis-server
```

### 2. Start Celery Worker
```bash
celery -A core worker -l info
```

### 3. Start Celery Beat (Scheduler)
```bash
celery -A core beat -l info
```

### 4. Start Django Server
```bash
python manage.py runserver
```

## Scheduled Tasks

### Auto-Checkout Tasks

#### General Auto-Checkout
- **Task**: `general_auto_checkout_task`
- **Schedule**: Every 5 minutes
- **Purpose**: Checks out employees at fixed time defined by organization
- **Configuration**: Set in `OrganizationSettings.auto_checkout_time`

#### Shift-Wise Auto-Checkout
- **Task**: `shiftwise_auto_checkout_task`
- **Schedule**: Every 5 minutes
- **Purpose**: Checks out employees based on shift end time + grace period
- **Configuration**: Set in `OrganizationSettings.auto_shiftwise_checkout_enabled`

### Periodic Tasks

#### Monthly Payroll Processing
- **Task**: `process_monthly_payroll_task`
- **Schedule**: 1st of every month at 2 AM
- **Purpose**: Process monthly payroll for all organizations

#### Leave Accrual Processing
- **Task**: `process_leave_accrual_task`
- **Schedule**: 1st of every month at 3 AM
- **Purpose**: Process leave accrual for all employees

#### Asset Depreciation Update
- **Task**: `update_asset_depreciation_task`
- **Schedule**: 1st of every month at 4 AM
- **Purpose**: Update asset depreciation values

#### Expense Reimbursement Processing
- **Task**: `process_expense_reimbursements_task`
- **Schedule**: Every Monday at 9 AM
- **Purpose**: Process pending expense reimbursements

#### Scheduled Notifications
- **Task**: `send_scheduled_notifications_task`
- **Schedule**: Every minute
- **Purpose**: Send scheduled notifications

#### Scheduled Broadcasts
- **Task**: `send_broadcast_notifications_task`
- **Schedule**: Every minute
- **Purpose**: Send scheduled broadcast messages

## Task Details

### Auto-Checkout Tasks

#### general_auto_checkout_task()
```python
@shared_task(name='general_auto_checkout_task')
def general_auto_checkout_task():
    """
    Handles general auto-checkout for organizations.
    Checks out all pending users at fixed time.
    """
```

**Logic:**
1. Get organizations with `auto_checkout_enabled=True` and `auto_shiftwise_checkout_enabled=False`
2. For each organization, check if current time >= `auto_checkout_time`
3. Find all pending attendances (check_in_time exists, check_out_time is null)
4. Set check_out_time to organization's auto_checkout_time
5. Calculate total_working_minutes
6. Update attendance records

#### shiftwise_auto_checkout_task()
```python
@shared_task(name='shiftwise_auto_checkout_task')
def shiftwise_auto_checkout_task():
    """
    Handles shift-wise auto-checkout for organizations.
    Checks out users based on shift end time + grace period.
    """
```

**Logic:**
1. Get organizations with `auto_shiftwise_checkout_enabled=True`
2. Find pending attendances with assigned shifts
3. For each attendance:
   - Calculate checkout time = shift end time + grace period
   - If current time >= checkout time, perform checkout
   - Handle night shifts (end time on next day)
4. Update attendance records

### Payroll Processing

#### process_monthly_payroll_task(org_id, month, year)
```python
@shared_task(name='process_monthly_payroll_task')
def process_monthly_payroll_task(org_id, month, year):
    """
    Process monthly payroll for an organization.
    """
```

**Logic:**
1. Get organization
2. Get all active employees
3. For each employee, calculate payroll using PayrollCalculator
4. Create payroll records
5. Generate payslips

### Leave Accrual

#### process_leave_accrual_task(org_id=None)
```python
@shared_task(name='process_leave_accrual_task')
def process_leave_accrual_task(org_id=None):
    """
    Process leave accrual for employees.
    """
```

**Logic:**
1. Get organizations (all or specific)
2. For each organization, get active employees
3. Process leave accrual based on leave policies
4. Update leave balances

### Notification Tasks

#### send_scheduled_notifications_task()
```python
@shared_task(name='send_scheduled_notifications_task')
def send_scheduled_notifications_task():
    """
    Send scheduled notifications.
    """
```

**Logic:**
1. Find notifications with `scheduled_at <= now` and `status='scheduled'`
2. Send notifications via configured channels (Email, SMS, Push)
3. Update notification status to 'sent' or 'failed'

## Manual Task Execution

### Execute Task Manually
```python
from core.tasks import general_auto_checkout_task

# Execute immediately
result = general_auto_checkout_task.delay()

# Execute at specific time
from datetime import datetime, timedelta
eta = datetime.now() + timedelta(hours=1)
result = general_auto_checkout_task.apply_async(eta=eta)
```

### Check Task Status
```python
# Get task result
result = general_auto_checkout_task.delay()
print(result.get())  # Wait for result
print(result.status)  # PENDING, SUCCESS, FAILURE
```

## Monitoring

### Celery Flower (Optional)
Install and run Flower for task monitoring:
```bash
pip install flower
celery -A core flower
```
Access at: http://localhost:5555

### Logs
Check Celery worker logs for task execution details:
```bash
celery -A core worker -l info --logfile=celery.log
```

## Troubleshooting

### Redis Connection Error
- Ensure Redis is running: `redis-cli ping` (should return PONG)
- Check Redis URL in settings
- Check firewall settings

### Tasks Not Executing
- Verify Celery worker is running
- Verify Celery beat is running (for scheduled tasks)
- Check task registration in logs
- Verify Redis connection

### Timezone Issues
- Ensure `CELERY_TIMEZONE` matches `TIME_ZONE` in settings
- Use timezone-aware datetimes in tasks
- Check system timezone

## Production Deployment

### Using Supervisor (Linux)
```ini
[program:celery_worker]
command=/path/to/venv/bin/celery -A core worker -l info
directory=/path/to/project
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/celery/worker.log

[program:celery_beat]
command=/path/to/venv/bin/celery -A core beat -l info
directory=/path/to/project
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/celery/beat.log
```

### Using Windows Service
Use NSSM (Non-Sucking Service Manager) to run Celery as Windows service.

## Best Practices

1. **Error Handling**: Always use try-except in tasks
2. **Logging**: Log important events in tasks
3. **Idempotency**: Make tasks idempotent (safe to retry)
4. **Timeouts**: Set appropriate task timeouts
5. **Resource Management**: Use database transactions where needed
6. **Monitoring**: Monitor task execution and failures
7. **Scaling**: Use multiple workers for high load

## Task Dependencies

Tasks can depend on other tasks:
```python
@shared_task
def task_a():
    return "A"

@shared_task
def task_b():
    return "B"

@shared_task
def task_c():
    a_result = task_a.delay()
    b_result = task_b.delay()
    return a_result.get() + b_result.get()
```

## Testing Tasks

```python
from django.test import TestCase
from core.tasks import general_auto_checkout_task

class TaskTestCase(TestCase):
    def test_auto_checkout(self):
        result = general_auto_checkout_task.delay()
        self.assertEqual(result.get()['status'], 'success')
```

## Security Considerations

1. **Task Authentication**: Ensure tasks verify user permissions
2. **Input Validation**: Validate all task inputs
3. **Rate Limiting**: Implement rate limiting for expensive tasks
4. **Resource Limits**: Set memory and CPU limits for workers
5. **Error Handling**: Don't expose sensitive information in errors

