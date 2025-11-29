"""
Advanced Task Management System
Comprehensive task tracking, assignments, and project management
"""

from django.db import models
from uuid import uuid4
from datetime import date, datetime
from AuthN.models import *


class TaskType(models.Model):
    """Task Type Master"""
    id = models.BigAutoField(primary_key=True)
    admin = models.ForeignKey(
        BaseUserModel, on_delete=models.CASCADE,
        limit_choices_to={'role': 'admin'},
        related_name="admin_task_type"
    )
    organization = models.ForeignKey(
        BaseUserModel, on_delete=models.CASCADE,
        limit_choices_to={'role': 'organization'},
        related_name="organization_task_type"
    )
    name = models.CharField(max_length=255, null=True, blank=True, default="Service Task")
    description = models.TextField(blank=True, null=True)
    color_code = models.CharField(max_length=7, default='#3498db')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name


class Project(models.Model):
    """Project Management"""
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    admin = models.ForeignKey(
        BaseUserModel, on_delete=models.CASCADE,
        limit_choices_to={'role': 'admin'},
        related_name='admin_projects'
    )
    organization = models.ForeignKey(
        BaseUserModel, on_delete=models.CASCADE,
        limit_choices_to={'role': 'organization'},
        related_name='org_projects'
    )
    
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    code = models.CharField(max_length=50, unique=True, blank=True, null=True)
    
    # Project Details
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ('planning', 'Planning'),
            ('in_progress', 'In Progress'),
            ('on_hold', 'On Hold'),
            ('completed', 'Completed'),
            ('cancelled', 'Cancelled')
        ],
        default='planning'
    )
    priority = models.CharField(
        max_length=20,
        choices=[
            ('low', 'Low'),
            ('medium', 'Medium'),
            ('high', 'High'),
            ('urgent', 'Urgent')
        ],
        default='medium'
    )
    
    # Team
    project_manager = models.ForeignKey(
        BaseUserModel, on_delete=models.SET_NULL,
        null=True, blank=True,
        limit_choices_to={'role': 'admin'},
        related_name='managed_projects'
    )
    team_members = models.ManyToManyField(
        BaseUserModel,
        limit_choices_to={'role': 'user'},
        related_name='assigned_projects',
        blank=True
    )
    
    # Budget
    estimated_budget = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    actual_budget = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    
    # Progress
    progress_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name


class Task(models.Model):
    """Task Model - Extended"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('on_hold', 'On Hold'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('review', 'Under Review')
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent')
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    admin = models.ForeignKey(
        BaseUserModel, on_delete=models.CASCADE,
        limit_choices_to={'role': 'admin'},
        related_name='admin_tasks'
    )
    organization = models.ForeignKey(
        BaseUserModel, on_delete=models.CASCADE,
        limit_choices_to={'role': 'organization'},
        related_name='org_tasks'
    )
    project = models.ForeignKey(
        Project, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='tasks'
    )
    task_type = models.ForeignKey(
        TaskType, on_delete=models.PROTECT,
        related_name='tasks'
    )
    
    # Task Details
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Assignment
    assigned_to = models.ForeignKey(
        BaseUserModel, on_delete=models.SET_NULL,
        null=True, blank=True,
        limit_choices_to={'role': 'user'},
        related_name='assigned_tasks'
    )
    assigned_by = models.ForeignKey(
        BaseUserModel, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='created_tasks'
    )
    
    # Timeline
    start_date = models.DateField(null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    estimated_hours = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    actual_hours = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Recurrence
    is_recurring = models.BooleanField(default=False)
    recurrence_frequency = models.CharField(
        max_length=50,
        choices=[
            ('daily', 'Daily'),
            ('weekly', 'Weekly'),
            ('monthly', 'Monthly'),
            ('yearly', 'Yearly')
        ],
        blank=True, null=True
    )
    recurrence_end_date = models.DateField(blank=True, null=True)
    week_day = models.CharField(max_length=20, blank=True, null=True)
    month_date = models.IntegerField(blank=True, null=True)
    
    # Additional
    tags = models.JSONField(default=list, blank=True)
    attachments = models.JSONField(default=list, blank=True)
    dependencies = models.ManyToManyField(
        'self',
        symmetrical=False,
        blank=True,
        related_name='dependent_tasks'
    )
    
    # Progress
    progress_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    checklist = models.JSONField(default=list, blank=True)
    
    # Comments & Notes
    comments = models.JSONField(default=list, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['assigned_to', 'status']),
            models.Index(fields=['due_date', 'status']),
            models.Index(fields=['project', 'status']),
        ]
    
    def __str__(self):
        return self.title


class TaskComment(models.Model):
    """Task Comments"""
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    task = models.ForeignKey(
        Task, on_delete=models.CASCADE,
        related_name='task_comments'
    )
    user = models.ForeignKey(
        BaseUserModel, on_delete=models.CASCADE,
        related_name='task_comments'
    )
    comment = models.TextField()
    attachments = models.JSONField(default=list, blank=True)
    is_internal = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Comment on {self.task.title}"


class TaskTimeLog(models.Model):
    """Task Time Logging"""
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    task = models.ForeignKey(
        Task, on_delete=models.CASCADE,
        related_name='time_logs'
    )
    user = models.ForeignKey(
        BaseUserModel, on_delete=models.CASCADE,
        related_name='task_time_logs'
    )
    
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True, blank=True)
    duration_minutes = models.IntegerField(null=True, blank=True)
    description = models.TextField(blank=True, null=True)
    is_billable = models.BooleanField(default=False)
    billing_rate = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-start_time']
    
    def __str__(self):
        return f"Time log - {self.task.title}"


class TaskAttachment(models.Model):
    """Task Attachments"""
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    task = models.ForeignKey(
        Task, on_delete=models.CASCADE,
        related_name='task_attachments'
    )
    uploaded_by = models.ForeignKey(
        BaseUserModel, on_delete=models.CASCADE,
        related_name='uploaded_task_attachments'
    )
    
    file_name = models.CharField(max_length=255)
    file_path = models.CharField(max_length=500)
    file_size = models.IntegerField(null=True, blank=True)
    file_type = models.CharField(max_length=50, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.file_name} - {self.task.title}"
