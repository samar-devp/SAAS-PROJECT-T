# Onboarding Management Module

## Overview
Comprehensive onboarding management system with templates, checklists, document collection, and automated task management.

## Features

### 1. Onboarding Templates
- Create reusable onboarding templates
- Department and designation-based templates
- Auto-create employee profile option
- Send welcome email option
- Assign default shift and location
- Usage tracking

### 2. Onboarding Checklists
- Template-based checklist items
- Task types (Document, Form, Training, Meeting, System Access)
- Assignment rules (Employee, HR, Manager, IT, Admin)
- Due date calculation (days from joining)
- Required vs optional tasks
- Auto-complete conditions

### 3. Onboarding Process
- Create onboarding process for new employees
- Track progress percentage
- Status management (Pending, In Progress, Completed, On Hold)
- Auto-create tasks from template
- Employee details before profile creation

### 4. Onboarding Tasks
- Individual task tracking
- Status management (Pending, In Progress, Completed, Skipped, Rejected)
- Due date tracking
- Document uploads
- Comments and rejection reasons
- Auto-update process progress

### 5. Document Types
- Define document types for collection
- KYC document support
- File format restrictions
- File size limits
- Expiry date requirements
- Verification requirements

### 6. Employee Documents
- Upload and manage employee documents
- Document verification workflow
- Expiry tracking
- Status management (Pending, Uploaded, Verified, Rejected, Expired)

## API Endpoints

### Onboarding Templates
```
GET    /api/onboarding/templates/<org_id>             - List templates
POST   /api/onboarding/templates/<org_id>             - Create template
GET    /api/onboarding/templates/<org_id>/<pk>        - Get template details
```

### Checklists
```
GET    /api/onboarding/checklists/<template_id>       - List checklist items
POST   /api/onboarding/checklists/<template_id>       - Add checklist item
```

### Onboarding Processes
```
GET    /api/onboarding/processes/<org_id>             - List processes
POST   /api/onboarding/processes/<org_id>             - Create process
GET    /api/onboarding/processes/<org_id>/<pk>        - Get process details
```

### Onboarding Tasks
```
GET    /api/onboarding/tasks/<process_id>             - List tasks
GET    /api/onboarding/tasks/<process_id>/<pk>        - Get task details
PUT    /api/onboarding/tasks/<process_id>/<pk>        - Update task
```

### Document Types
```
GET    /api/onboarding/document-types/<org_id>        - List document types
POST   /api/onboarding/document-types/<org_id>        - Create document type
GET    /api/onboarding/document-types/<org_id>/<pk>   - Get document type details
```

### Employee Documents
```
GET    /api/onboarding/documents/<employee_id>        - List documents
POST   /api/onboarding/documents/<employee_id>        - Upload document
GET    /api/onboarding/documents/<employee_id>/<pk>   - Get document details
```

## Query Parameters

### Processes List
- `status` - Filter by status

### Tasks List
- `status` - Filter by status

### Documents List
- `status` - Filter by status

## Models

- **OnboardingTemplate** - Onboarding templates
- **OnboardingChecklist** - Checklist items
- **OnboardingProcess** - Onboarding processes
- **OnboardingTask** - Individual tasks
- **DocumentType** - Document types
- **EmployeeDocument** - Employee documents

## Usage Example

```python
# Create onboarding process
POST /api/onboarding/processes/<org_id>
{
    "employee_name": "John Doe",
    "employee_email": "john@example.com",
    "joining_date": "2024-01-15",
    "template_id": "<template_id>",
    "department": "Engineering",
    "designation": "Software Engineer"
}

# Update task status
PUT /api/onboarding/tasks/<process_id>/<task_id>
{
    "status": "completed",
    "comments": "Document verified and approved"
}

# Upload document
POST /api/onboarding/documents/<employee_id>
{
    "document_type_id": "<doc_type_id>",
    "document_name": "Aadhaar Card",
    "file_path": "/uploads/aadhaar.pdf",
    "issue_date": "2020-01-01",
    "expiry_date": null
}
```

