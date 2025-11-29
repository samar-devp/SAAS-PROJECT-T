# Organization Management Module

## Overview
Comprehensive organization management system for subscription plans, module access control, usage tracking, and super admin features.

## Features

### 1. Subscription Plans
- Create subscription plans
- Pricing (Monthly, Quarterly, Yearly)
- Employee limits
- Storage limits
- API call limits
- Enabled modules configuration
- Grace period settings

### 2. Organization Subscriptions
- Assign plans to organizations
- Subscription status tracking
- Expiry date management
- Grace period tracking
- Payment status
- Auto-renewal settings
- Custom limits override

### 3. Module Access Control
- Enable/disable modules per organization
- Module-specific limits
- Enable/disable timestamps
- Custom module configuration

### 4. Usage Statistics
- Period-based usage tracking
- Employee count
- Storage usage
- API calls count
- Feature usage metrics
- Attendance records count
- Payroll runs count

### 5. Organization Deactivation
- Deactivation reasons (Payment Failed, Expired, Policy Violation, etc.)
- Deactivation logging
- Reactivation support
- Grace period handling

### 6. Super Admin Actions
- Action logging
- Organization management
- Plan assignment
- Module management
- Limit management
- Force logout
- Data export tracking

## API Endpoints

### Subscription Plans
```
GET    /api/organization/plans                        - List plans
POST   /api/organization/plans                        - Create plan
GET    /api/organization/plans/<pk>                   - Get plan details
```

### Organization Subscriptions
```
GET    /api/organization/subscriptions/<org_id>       - Get subscription
POST   /api/organization/subscriptions/<org_id>       - Assign/Update subscription
```

### Organization Modules
```
GET    /api/organization/modules/<org_id>             - List modules
POST   /api/organization/modules/<org_id>             - Enable/Disable module
GET    /api/organization/modules/<org_id>/<pk>        - Get module details
```

### Organization Usage
```
GET    /api/organization/usage/<org_id>               - Get usage statistics
```

### Organization Deactivation
```
POST   /api/organization/deactivate/<org_id>          - Deactivate organization
DELETE /api/organization/deactivate/<org_id>          - Reactivate organization
```

## Query Parameters

### Usage Statistics
- `period_type` - daily, monthly, yearly
- `period_start` - Start date

## Models

- **SubscriptionPlan** - Subscription plans
- **OrganizationSubscription** - Organization subscriptions
- **OrganizationModule** - Module access control
- **OrganizationUsage** - Usage statistics
- **OrganizationDeactivationLog** - Deactivation history
- **SuperAdminAction** - Super admin action logs

## Usage Example

```python
# Assign subscription to organization
POST /api/organization/subscriptions/<org_id>
{
    "plan_id": "<plan_id>",
    "start_date": "2024-01-01"
}

# Enable module
POST /api/organization/modules/<org_id>
{
    "module_code": "payroll",
    "module_name": "Payroll Management",
    "is_enabled": true
}

# Deactivate organization
POST /api/organization/deactivate/<org_id>
{
    "reason": "payment_failed",
    "reason_description": "Payment failed for 3 consecutive months"
}
```

## Celery Tasks

### Organization Expiry Check
- Runs daily at 6 AM
- Checks organization expiry dates
- Deactivates expired organizations
- Sends grace period reminders

### Renewal Reminders
- Runs daily at 9 AM
- Sends reminders 7, 3, 1 days before expiry
- Email notifications

## Super Admin Features

1. **Create Organizations** - Create new organization accounts
2. **Activate/Deactivate** - Manage organization status
3. **Assign Plans** - Assign subscription plans
4. **Module Management** - Enable/disable modules per org
5. **Limit Management** - Increase employee/storage/API limits
6. **Usage Statistics** - View organization usage
7. **Action Logging** - Track all super admin actions
8. **Force Logout** - Force logout all users of an organization
9. **Data Export** - Export organization data

