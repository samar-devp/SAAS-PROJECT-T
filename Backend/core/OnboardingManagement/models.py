"""
Advanced Onboarding Management System
Document collection, Auto employee profile creation, Task checklist automation
"""

from django.db import models
from uuid import uuid4
from decimal import Decimal
from datetime import date, datetime
from AuthN.models import *


class OnboardingTemplate(models.Model):
    """Onboarding Templates"""
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    organization = models.ForeignKey(
        BaseUserModel, on_delete=models.CASCADE,
        limit_choices_to={'role': 'organization'},
        related_name='onboarding_templates'
    )
    admin = models.ForeignKey(
        BaseUserModel, on_delete=models.CASCADE,
        limit_choices_to={'role': 'admin'},
        related_name='admin_onboarding_templates',
        null=True, blank=True
    )
    
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    department = models.CharField(max_length=100, blank=True, null=True)
    designation = models.CharField(max_length=100, blank=True, null=True)
    
    # Template Settings
    auto_create_profile = models.BooleanField(default=True)
    send_welcome_email = models.BooleanField(default=True)
    assign_default_shift = models.BooleanField(default=True)
    assign_default_location = models.BooleanField(default=True)
    
    is_active = models.BooleanField(default=True)
    usage_count = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name


class OnboardingChecklist(models.Model):
    """Onboarding Checklist Items"""
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    template = models.ForeignKey(
        OnboardingTemplate, on_delete=models.CASCADE,
        related_name='checklist_items'
    )
    
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    task_type = models.CharField(
        max_length=50,
        choices=[
            ('document', 'Document Collection'),
            ('form', 'Form Filling'),
            ('training', 'Training'),
            ('meeting', 'Meeting'),
            ('system_access', 'System Access'),
            ('other', 'Other')
        ],
        default='document'
    )
    
    # Assignment
    assigned_to = models.CharField(
        max_length=50,
        choices=[
            ('employee', 'Employee'),
            ('hr', 'HR Team'),
            ('manager', 'Manager'),
            ('it', 'IT Team'),
            ('admin', 'Admin')
        ],
        default='employee'
    )
    
    # Requirements
    is_required = models.BooleanField(default=True)
    due_days = models.IntegerField(default=7, help_text="Days from joining date")
    
    # Document Requirements
    document_type = models.CharField(max_length=100, blank=True, null=True)
    file_formats = models.JSONField(default=list, blank=True, help_text="['pdf', 'jpg', 'png']")
    max_file_size_mb = models.IntegerField(default=5)
    
    # Automation
    auto_complete = models.BooleanField(default=False)
    auto_complete_condition = models.JSONField(default=dict, blank=True)
    
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['order', 'title']
    
    def __str__(self):
        return f"{self.template.name} - {self.title}"


class OnboardingProcess(models.Model):
    """Onboarding Process for New Employee"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('on_hold', 'On Hold'),
        ('cancelled', 'Cancelled')
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    organization = models.ForeignKey(
        BaseUserModel, on_delete=models.CASCADE,
        limit_choices_to={'role': 'organization'},
        related_name='onboarding_processes'
    )
    employee = models.ForeignKey(
        BaseUserModel, on_delete=models.CASCADE,
        limit_choices_to={'role': 'user'},
        related_name='onboarding_process',
        null=True, blank=True
    )
    template = models.ForeignKey(
        OnboardingTemplate, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='processes'
    )
    
    # Employee Details (before profile creation)
    employee_name = models.CharField(max_length=255)
    employee_email = models.EmailField()
    employee_phone = models.CharField(max_length=20, blank=True, null=True)
    joining_date = models.DateField()
    department = models.CharField(max_length=100, blank=True, null=True)
    designation = models.CharField(max_length=100, blank=True, null=True)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    progress_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    
    # Dates
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Assigned To
    assigned_to = models.ForeignKey(
        BaseUserModel, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='assigned_onboardings',
        limit_choices_to={'role': 'admin'}
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Onboarding - {self.employee_name}"


class OnboardingTask(models.Model):
    """Individual Onboarding Tasks"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('skipped', 'Skipped'),
        ('rejected', 'Rejected')
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    onboarding_process = models.ForeignKey(
        OnboardingProcess, on_delete=models.CASCADE,
        related_name='tasks'
    )
    checklist_item = models.ForeignKey(
        OnboardingChecklist, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='tasks'
    )
    
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    task_type = models.CharField(max_length=50, default='document')
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Assignment
    assigned_to = models.ForeignKey(
        BaseUserModel, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='onboarding_tasks'
    )
    
    # Due Date
    due_date = models.DateField()
    completed_at = models.DateTimeField(null=True, blank=True)
    completed_by = models.ForeignKey(
        BaseUserModel, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='completed_onboarding_tasks'
    )
    
    # Documents
    documents = models.JSONField(default=list, blank=True, help_text="List of uploaded document paths")
    
    # Comments
    comments = models.TextField(blank=True, null=True)
    rejection_reason = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['due_date', 'created_at']
    
    def __str__(self):
        return f"{self.onboarding_process.employee_name} - {self.title}"


class DocumentType(models.Model):
    """Document Types for Collection"""
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    organization = models.ForeignKey(
        BaseUserModel, on_delete=models.CASCADE,
        limit_choices_to={'role': 'organization'},
        related_name='document_types'
    )
    
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    
    # Requirements
    is_required = models.BooleanField(default=True)
    file_formats = models.JSONField(default=list, blank=True)
    max_file_size_mb = models.IntegerField(default=5)
    expiry_required = models.BooleanField(default=False)
    verification_required = models.BooleanField(default=False)
    
    # KYC Documents
    is_kyc_document = models.BooleanField(default=False)
    kyc_type = models.CharField(
        max_length=50,
        choices=[
            ('identity', 'Identity Proof'),
            ('address', 'Address Proof'),
            ('education', 'Education Proof'),
            ('employment', 'Employment Proof'),
            ('other', 'Other')
        ],
        blank=True, null=True
    )
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('organization', 'code') if 'code' else None
        ordering = ['name']
    
    def __str__(self):
        return self.name


class EmployeeDocument(models.Model):
    """Employee Documents"""
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    employee = models.ForeignKey(
        BaseUserModel, on_delete=models.CASCADE,
        limit_choices_to={'role': 'user'},
        related_name='documents'
    )
    document_type = models.ForeignKey(
        DocumentType, on_delete=models.PROTECT,
        related_name='employee_documents'
    )
    
    # Document Details
    document_name = models.CharField(max_length=255)
    file_path = models.CharField(max_length=500)
    file_size = models.IntegerField(null=True, blank=True)
    file_type = models.CharField(max_length=50, blank=True, null=True)
    
    # Dates
    issue_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    
    # Verification
    is_verified = models.BooleanField(default=False)
    verified_by = models.ForeignKey(
        BaseUserModel, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='verified_documents'
    )
    verified_at = models.DateTimeField(null=True, blank=True)
    verification_notes = models.TextField(blank=True, null=True)
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('uploaded', 'Uploaded'),
            ('verified', 'Verified'),
            ('rejected', 'Rejected'),
            ('expired', 'Expired')
        ],
        default='pending'
    )
    
    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f"{self.employee.email} - {self.document_type.name}"

