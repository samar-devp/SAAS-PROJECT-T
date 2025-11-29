"""
Advanced Visit Management System
Comprehensive visit scheduling, tracking, and reporting
"""

from django.db import models
from uuid import uuid4
from decimal import Decimal
from datetime import date, datetime
from AuthN.models import *


class VisitAssignment(models.Model):
    """Visit Assignment - Extended"""
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('rescheduled', 'Rescheduled'),
        ('no_show', 'No Show')
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
        related_name='admin_visits'
    )
    organization = models.ForeignKey(
        BaseUserModel, on_delete=models.CASCADE,
        limit_choices_to={'role': 'organization'},
        related_name='org_visits'
    )
    assigned_user = models.ForeignKey(
        BaseUserModel, on_delete=models.CASCADE,
        limit_choices_to={'role': 'user'},
        related_name='assigned_visits'
    )
    
    # Visitor Information
    visitor_name = models.CharField(max_length=255)
    company_name = models.CharField(max_length=255)
    visitor_email = models.EmailField()
    visitor_mobile = models.CharField(max_length=15)
    visitor_alternate_mobile = models.CharField(max_length=15, blank=True, null=True)
    job_title = models.CharField(max_length=255, blank=True, null=True)
    
    # Visit Details
    visit_type = models.CharField(max_length=100, blank=True, null=True)  # Sales, Support, Follow-up, etc.
    purpose = models.TextField()
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    
    # Location Details
    address = models.TextField()
    district = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100, blank=True, null=True)
    pincode = models.CharField(max_length=10, blank=True, null=True)
    segment = models.CharField(max_length=100, blank=True, null=True)
    
    # Schedule
    meeting_date = models.DateField()
    meeting_time = models.TimeField()
    scheduled_start_time = models.DateTimeField()
    scheduled_end_time = models.DateTimeField()
    actual_start_time = models.DateTimeField(null=True, blank=True)
    actual_end_time = models.DateTimeField(null=True, blank=True)
    duration_minutes = models.IntegerField(null=True, blank=True)
    
    # Location Tracking
    start_latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    start_longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    end_latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    end_longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    distance_traveled_km = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Visit Outcome
    review = models.CharField(max_length=255, blank=True, null=True)
    rating = models.IntegerField(null=True, blank=True, help_text="Rating out of 5")
    comment = models.TextField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    outcome = models.CharField(max_length=100, blank=True, null=True)  # Successful, Follow-up Required, etc.
    next_follow_up_date = models.DateField(null=True, blank=True)
    
    # Documents & Attachments
    attachments = models.JSONField(default=list, blank=True)
    photos = models.JSONField(default=list, blank=True)
    documents = models.JSONField(default=list, blank=True)
    
    # Additional Fields
    estimated_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    actual_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    expenses = models.JSONField(default=list, blank=True)
    
    # Reminders & Notifications
    reminder_sent = models.BooleanField(default=False)
    reminder_sent_at = models.DateTimeField(null=True, blank=True)
    
    # Cancellation
    cancelled_at = models.DateTimeField(null=True, blank=True)
    cancelled_by = models.ForeignKey(
        BaseUserModel, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='cancelled_visits'
    )
    cancellation_reason = models.TextField(blank=True, null=True)
    
    # Rescheduling
    rescheduled_from = models.DateTimeField(null=True, blank=True)
    reschedule_count = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        BaseUserModel, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='created_visits'
    )
    
    class Meta:
        ordering = ['-meeting_date', '-meeting_time']
        indexes = [
            models.Index(fields=['assigned_user', 'status']),
            models.Index(fields=['meeting_date', 'status']),
            models.Index(fields=['organization', 'status']),
        ]
    
    def __str__(self):
        return f"{self.visitor_name} - {self.company_name} ({self.meeting_date})"


class VisitTemplate(models.Model):
    """Visit Templates for recurring visits"""
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    admin = models.ForeignKey(
        BaseUserModel, on_delete=models.CASCADE,
        limit_choices_to={'role': 'admin'},
        related_name='admin_visit_templates'
    )
    organization = models.ForeignKey(
        BaseUserModel, on_delete=models.CASCADE,
        limit_choices_to={'role': 'organization'},
        related_name='org_visit_templates'
    )
    
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    visit_type = models.CharField(max_length=100)
    default_duration_minutes = models.IntegerField(default=60)
    default_purpose = models.TextField(blank=True, null=True)
    checklist = models.JSONField(default=list, blank=True)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name


class VisitChecklist(models.Model):
    """Visit Checklist Items"""
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    visit = models.ForeignKey(
        VisitAssignment, on_delete=models.CASCADE,
        related_name='checklist_items'
    )
    item = models.CharField(max_length=255)
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True, null=True)
    order = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['order', 'created_at']
    
    def __str__(self):
        return f"{self.visit.visitor_name} - {self.item}"


class VisitReport(models.Model):
    """Visit Reports and Analytics"""
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    visit = models.OneToOneField(
        VisitAssignment, on_delete=models.CASCADE,
        related_name='report'
    )
    
    # Report Details
    summary = models.TextField()
    key_findings = models.JSONField(default=list, blank=True)
    recommendations = models.TextField(blank=True, null=True)
    action_items = models.JSONField(default=list, blank=True)
    
    # Metrics
    customer_satisfaction_score = models.IntegerField(null=True, blank=True)
    visit_effectiveness = models.CharField(max_length=50, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        BaseUserModel, on_delete=models.SET_NULL,
        null=True, blank=True
    )
    
    def __str__(self):
        return f"Report - {self.visit.visitor_name}"
