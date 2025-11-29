# HR Analytics Module

## Overview
Comprehensive HR analytics system for attendance, attrition, cost center, and salary distribution analysis.

## Features

### 1. Cost Center Management
- Create and manage cost centers
- Hierarchical cost center structure
- Annual budget allocation
- Parent-child relationships

### 2. Attendance Analytics
- Aggregated attendance metrics
- Period-based analytics (Daily, Weekly, Monthly, Yearly)
- Present/Absent/Leave days tracking
- Late and early exit counts
- Working hours calculation
- Attendance rate calculation
- Punctuality rate calculation

### 3. Attrition Management
- Record employee separations
- Separation types (Resignation, Termination, Retirement, etc.)
- Reason categorization
- Tenure calculation
- Exit interview tracking
- Attrition analytics aggregation

### 4. Attrition Analytics
- Period-based attrition reports
- Attrition rate calculation
- Department-wise breakdown
- Reason-wise breakdown
- Average tenure analysis

### 5. Salary Distribution
- Period-based salary analysis
- Total payroll cost
- Average, median, min, max salary
- Department-wise distribution
- Designation-wise distribution
- Salary band analysis

### 6. Cost Center Analytics
- Period-based cost analysis
- Payroll cost tracking
- Operational cost tracking
- Budget utilization
- Cost per employee
- Budget vs Actual reports

## API Endpoints

### Cost Centers
```
GET    /api/analytics/cost-centers/<org_id>           - List cost centers
POST   /api/analytics/cost-centers/<org_id>           - Create cost center
GET    /api/analytics/cost-centers/<org_id>/<pk>      - Get cost center details
```

### Attendance Analytics
```
GET    /api/analytics/attendance/<org_id>             - Get analytics
POST   /api/analytics/attendance/<org_id>             - Generate analytics
```

### Attrition Records
```
GET    /api/analytics/attrition/<org_id>              - List records
POST   /api/analytics/attrition/<org_id>              - Create record
GET    /api/analytics/attrition/<org_id>/<pk>         - Get record details
```

### Salary Distribution
```
GET    /api/analytics/salary-distribution/<org_id>    - Get distribution
POST   /api/analytics/salary-distribution/<org_id>    - Generate distribution
```

## Query Parameters

### Attendance Analytics
- `period_type` - daily, weekly, monthly, yearly
- `period_start` - Start date
- `period_end` - End date
- `employee_id` - Filter by employee

### Salary Distribution
- `period_type` - monthly, quarterly, yearly
- `period_start` - Start date
- `period_end` - End date
- `month` - Month number (1-12)
- `year` - Year

## Models

- **CostCenter** - Cost centers
- **AttendanceAnalytics** - Attendance analytics
- **AttritionRecord** - Attrition records
- **AttritionAnalytics** - Attrition analytics
- **SalaryDistribution** - Salary distribution
- **CostCenterAnalytics** - Cost center analytics

## Usage Example

```python
# Generate attendance analytics
POST /api/analytics/attendance/<org_id>
{
    "period_type": "monthly",
    "period_start": "2024-01-01",
    "period_end": "2024-01-31"
}

# Create attrition record
POST /api/analytics/attrition/<org_id>
{
    "employee_id": "<employee_id>",
    "separation_type": "resignation",
    "separation_date": "2024-01-31",
    "last_working_date": "2024-01-31",
    "reason": "Better opportunity",
    "reason_category": "better_opportunity"
}

# Generate salary distribution
POST /api/analytics/salary-distribution/<org_id>
{
    "period_type": "monthly",
    "month": 1,
    "year": 2024
}
```

