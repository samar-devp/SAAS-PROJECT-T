# Performance Management Module

## Overview
Comprehensive performance management system with OKRs, KPIs, goal library, review cycles, and 360-degree reviews.

## Features

### 1. Goal Library
- Predefined goals for reuse
- Category and department-based goals
- Metric types (Percentage, Number, Currency, Boolean, Rating)
- Usage tracking

### 2. OKRs (Objectives and Key Results)
- Set objectives with key results
- Period-based (Quarterly, Half-Yearly, Yearly)
- Progress tracking
- Status management (Not Started, On Track, At Risk, Completed)
- Review and feedback

### 3. KPIs (Key Performance Indicators)
- Employee-specific KPIs
- Target vs Current value tracking
- Status calculation (Below Target, On Target, Above Target)
- Period-based tracking (Monthly, Quarterly, Yearly)
- Multiple metric types

### 4. Review Cycles
- Create review cycles (Monthly, Quarterly, Half-Yearly, Yearly)
- Self-review period
- Manager review period
- HR review period
- Enable/disable 360 reviews
- Enable/disable peer reviews

### 5. Performance Reviews
- Multiple review types (Self, Manager, Peer, HR, 360)
- Section-based ratings
- Overall rating calculation
- Strengths and areas for improvement
- Development plans
- Feedback and comments

### 6. 360 Degree Reviews
- Multi-source feedback
- Relationship-based reviews (Peer, Subordinate, Manager, Client)
- Anonymous reviews
- Comprehensive feedback collection

### 7. Rating Matrix
- Customizable rating scales
- Default rating matrix
- Score-based rating labels

## API Endpoints

### Goal Library
```
GET    /api/performance/goals/<org_id>                - List goals
POST   /api/performance/goals/<org_id>                - Create goal
GET    /api/performance/goals/<org_id>/<pk>           - Get goal details
```

### OKRs
```
GET    /api/performance/okrs/<org_id>                 - List OKRs
POST   /api/performance/okrs/<org_id>                 - Create OKR
GET    /api/performance/okrs/<org_id>/<pk>            - Get OKR details
PUT    /api/performance/okrs/<org_id>/<pk>            - Update OKR
```

### KPIs
```
GET    /api/performance/kpis/<org_id>                 - List KPIs
POST   /api/performance/kpis/<org_id>                 - Create KPI
GET    /api/performance/kpis/<org_id>/<pk>            - Get KPI details
```

### Review Cycles
```
GET    /api/performance/review-cycles/<org_id>        - List cycles
POST   /api/performance/review-cycles/<org_id>        - Create cycle
GET    /api/performance/review-cycles/<org_id>/<pk>   - Get cycle details
```

### Performance Reviews
```
GET    /api/performance/reviews/<org_id>              - List reviews
POST   /api/performance/reviews/<org_id>              - Create review
GET    /api/performance/reviews/<org_id>/<pk>         - Get review details
```

## Query Parameters

### OKRs List
- `employee_id` - Filter by employee
- `status` - Filter by status
- `period_type` - Filter by period type

### Performance Reviews List
- `employee_id` - Filter by employee
- `reviewer_id` - Filter by reviewer
- `review_type` - Filter by review type
- `status` - Filter by status

## Models

- **GoalLibrary** - Predefined goals
- **OKR** - Objectives and Key Results
- **KPI** - Key Performance Indicators
- **ReviewCycle** - Review cycles
- **RatingMatrix** - Rating scales
- **PerformanceReview** - Performance reviews
- **Review360** - 360-degree reviews

## Usage Example

```python
# Create OKR
POST /api/performance/okrs/<org_id>
{
    "employee_id": "<employee_id>",
    "objective": "Increase customer satisfaction",
    "key_results": [
        {"name": "CSAT Score", "target": 4.5, "current": 4.2},
        {"name": "Response Time", "target": 2, "current": 3}
    ],
    "period_type": "quarterly",
    "period_start": "2024-01-01",
    "period_end": "2024-03-31"
}

# Create Performance Review
POST /api/performance/reviews/<org_id>
{
    "employee_id": "<employee_id>",
    "reviewer_id": "<reviewer_id>",
    "review_cycle_id": "<cycle_id>",
    "review_type": "manager",
    "section_ratings": {
        "technical_skills": 4.5,
        "communication": 4.0
    },
    "overall_rating": 4.25
}
```

