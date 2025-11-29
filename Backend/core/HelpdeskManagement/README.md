# Helpdesk Management Module

## Overview
Advanced helpdesk management system with ticket creation, SLA management, auto-escalation, and assignment rules.

## Features

### 1. Ticket Categories
- Create and manage ticket categories
- Set default SLA hours per category
- Priority-based categorization
- Active/Inactive status management

### 2. Ticket Management
- Create, update, and track tickets
- Automatic ticket number generation
- Status workflow (Open → Assigned → In Progress → Resolved → Closed)
- Priority levels (Low, Medium, High, Critical)
- SLA deadline tracking
- First response time tracking
- Resolution time tracking

### 3. Ticket Comments
- Add comments to tickets
- Internal notes (not visible to customer)
- File attachments support
- Comment history tracking

### 4. Auto Assignment Rules
- Rule-based ticket assignment
- Priority-based assignment
- Category-based assignment
- Round-robin assignment
- Custom assignment conditions (JSON)

### 5. SLA Policies
- Configurable SLA policies
- First response time (hours)
- Resolution time (hours)
- Escalation rules
- Business hours support
- Escalation to specific users

### 6. Escalation Management
- Automatic escalation based on SLA
- Escalation level tracking
- Escalation history logs
- Multi-level escalation support

## API Endpoints

### Ticket Categories
```
GET    /api/helpdesk/categories/<org_id>              - List all categories
POST   /api/helpdesk/categories/<org_id>              - Create category
GET    /api/helpdesk/categories/<org_id>/<pk>         - Get category details
```

### Tickets
```
GET    /api/helpdesk/tickets/<org_id>                 - List tickets (with filters)
POST   /api/helpdesk/tickets/<org_id>                 - Create ticket
GET    /api/helpdesk/tickets/<org_id>/<pk>            - Get ticket details
PUT    /api/helpdesk/tickets/<org_id>/<pk>            - Update ticket
```

### Ticket Comments
```
GET    /api/helpdesk/tickets/<ticket_id>/comments     - Get comments
POST   /api/helpdesk/tickets/<ticket_id>/comments     - Add comment
```

## Query Parameters

### Tickets List
- `status` - Filter by status (open, assigned, in_progress, resolved, closed, cancelled)
- `priority` - Filter by priority (low, medium, high, critical)
- `assigned_to` - Filter by assigned user ID

## Models

- **TicketCategory** - Ticket categories
- **Ticket** - Support tickets
- **TicketComment** - Ticket comments/updates
- **TicketAssignmentRule** - Auto assignment rules
- **SLAPolicy** - SLA policies
- **TicketEscalationLog** - Escalation history

## Usage Example

```python
# Create a ticket
POST /api/helpdesk/tickets/<org_id>
{
    "title": "Login Issue",
    "description": "Unable to login to the system",
    "category": "<category_id>",
    "priority": "high",
    "created_by": "<user_id>",
    "admin_id": "<admin_id>"
}

# Add comment to ticket
POST /api/helpdesk/tickets/<ticket_id>/comments
{
    "comment": "Issue resolved. User can now login.",
    "is_internal": false
}
```

