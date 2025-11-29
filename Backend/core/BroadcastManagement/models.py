"""
Advanced Broadcast Management System
Comprehensive announcement and communication system
"""

from django.db import models
from uuid import uuid4
from datetime import date, datetime
from AuthN.models import *


class Broadcast(models.Model):
    """Broadcast/Announcement Model"""
    TYPE_CHOICES = [
        ('announcement', 'Announcement'),
        ('notification', 'Notification'),
        ('alert', 'Alert'),
        ('update', 'Update'),
        ('event', 'Event'),
        ('policy', 'Policy'),
        ('reminder', 'Reminder')
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent')
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('scheduled', 'Scheduled'),
        ('published', 'Published'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled')
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    admin = models.ForeignKey(
        BaseUserModel, on_delete=models.CASCADE,
        limit_choices_to={'role': 'admin'},
        related_name='admin_broadcasts'
    )
    organization = models.ForeignKey(
        BaseUserModel, on_delete=models.CASCADE,
        limit_choices_to={'role': 'organization'},
        related_name='org_broadcasts'
    )
    created_by = models.ForeignKey(
        BaseUserModel, on_delete=models.CASCADE,
        related_name='created_broadcasts'
    )
    
    # Broadcast Details
    title = models.CharField(max_length=255)
    message = models.TextField()
    short_description = models.TextField(blank=True, null=True)
    broadcast_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='announcement')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Targeting
    target_audience = models.CharField(
        max_length=20,
        choices=[
            ('all', 'All Employees'),
            ('department', 'Specific Department'),
            ('designation', 'Specific Designation'),
            ('individual', 'Specific Individuals'),
            ('custom', 'Custom Group')
        ],
        default='all'
    )
    target_departments = models.JSONField(default=list, blank=True)
    target_designations = models.JSONField(default=list, blank=True)
    target_users = models.ManyToManyField(
        BaseUserModel,
        related_name='targeted_broadcasts',
        blank=True
    )
    
    # Schedule
    publish_date = models.DateTimeField(null=True, blank=True)
    expiry_date = models.DateTimeField(null=True, blank=True)
    is_recurring = models.BooleanField(default=False)
    recurrence_pattern = models.CharField(max_length=50, blank=True, null=True)
    
    # Media & Attachments
    image = models.CharField(max_length=500, blank=True, null=True)
    attachments = models.JSONField(default=list, blank=True)
    links = models.JSONField(default=list, blank=True)
    
    # Actions
    action_url = models.CharField(max_length=500, blank=True, null=True)
    action_text = models.CharField(max_length=100, blank=True, null=True)
    requires_acknowledgment = models.BooleanField(default=False)
    
    # Delivery
    send_email = models.BooleanField(default=False)
    send_sms = models.BooleanField(default=False)
    send_push = models.BooleanField(default=True)
    send_in_app = models.BooleanField(default=True)
    
    # Statistics
    total_recipients = models.IntegerField(default=0)
    read_count = models.IntegerField(default=0)
    acknowledged_count = models.IntegerField(default=0)
    
    # Metadata
    tags = models.JSONField(default=list, blank=True)
    category = models.CharField(max_length=100, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'publish_date']),
            models.Index(fields=['organization', 'status']),
        ]
    
    def __str__(self):
        return self.title


class BroadcastRecipient(models.Model):
    """Broadcast Recipient Tracking"""
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    broadcast = models.ForeignKey(
        Broadcast, on_delete=models.CASCADE,
        related_name='recipients'
    )
    user = models.ForeignKey(
        BaseUserModel, on_delete=models.CASCADE,
        related_name='broadcast_recipients'
    )
    
    # Status
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    is_acknowledged = models.BooleanField(default=False)
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    
    # Delivery Status
    email_sent = models.BooleanField(default=False)
    email_sent_at = models.DateTimeField(null=True, blank=True)
    sms_sent = models.BooleanField(default=False)
    sms_sent_at = models.DateTimeField(null=True, blank=True)
    push_sent = models.BooleanField(default=False)
    push_sent_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('broadcast', 'user')
        indexes = [
            models.Index(fields=['user', 'is_read']),
        ]
    
    def __str__(self):
        return f"{self.broadcast.title} - {self.user.email}"


class BroadcastTemplate(models.Model):
    """Broadcast Templates"""
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    admin = models.ForeignKey(
        BaseUserModel, on_delete=models.CASCADE,
        limit_choices_to={'role': 'admin'},
        related_name='admin_broadcast_templates'
    )
    organization = models.ForeignKey(
        BaseUserModel, on_delete=models.CASCADE,
        limit_choices_to={'role': 'organization'},
        related_name='org_broadcast_templates'
    )
    
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    template_title = models.CharField(max_length=255)
    template_message = models.TextField()
    broadcast_type = models.CharField(max_length=20, default='announcement')
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name

