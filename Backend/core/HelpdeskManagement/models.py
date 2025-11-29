"""
Advanced Helpdesk Management System
Ticket creation, assignment rules, auto-escalation, SLA engine
"""

from django.db import models
from uuid import uuid4
from decimal import Decimal
from datetime import date, datetime, timedelta
from AuthN.models import *


class TicketCategory(models.Model):
    """Ticket Categories"""
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    organization = models.ForeignKey(
        BaseUserModel, on_delete=models.CASCADE,
        limit_choices_to={'role': 'organization'},
        related_name='ticket_categories'
    )
    admin = models.ForeignKey(
        BaseUserModel, on_delete=models.CASCADE,
        limit_choices_to={'role': 'admin'},
        related_name='admin_ticket_categories',
        null=True, blank=True
    )
    
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    code = models.CharField(max_length=50, blank=True, null=True)
    priority = models.CharField(
        max_length=20,
        choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High'), ('critical', 'Critical')],
        default='medium'
    )
    default_sla_hours = models.IntegerField(default=24, help_text="Default SLA in hours")
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('organization', 'code') if 'code' else None
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Ticket(models.Model):
    """Support Tickets"""
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('assigned', 'Assigned'),
        ('in_progress', 'In Progress'),
        ('pending', 'Pending Customer'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
        ('cancelled', 'Cancelled')
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical')
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    organization = models.ForeignKey(
        BaseUserModel, on_delete=models.CASCADE,
        limit_choices_to={'role': 'organization'},
        related_name='org_tickets'
    )
    admin = models.ForeignKey(
        BaseUserModel, on_delete=models.CASCADE,
        limit_choices_to={'role': 'admin'},
        related_name='admin_tickets',
        null=True, blank=True
    )
    
    # Ticket Details
    ticket_number = models.CharField(max_length=50, unique=True)
    title = models.CharField(max_length=255)
    description = models.TextField()
    category = models.ForeignKey(
        TicketCategory, on_delete=models.PROTECT,
        related_name='tickets',
        null=True, blank=True
    )
    
    # Status & Priority
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    
    # Assignment
    created_by = models.ForeignKey(
        BaseUserModel, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='created_tickets',
        limit_choices_to={'role': 'user'}
    )
    assigned_to = models.ForeignKey(
        BaseUserModel, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='assigned_tickets',
        limit_choices_to={'role__in': ['admin', 'user']}
    )
    assigned_at = models.DateTimeField(null=True, blank=True)
    
    # SLA Management
    sla_hours = models.IntegerField(default=24)
    sla_deadline = models.DateTimeField(null=True, blank=True)
    sla_status = models.CharField(
        max_length=20,
        choices=[('on_time', 'On Time'), ('at_risk', 'At Risk'), ('breached', 'Breached')],
        default='on_time'
    )
    first_response_time = models.DateTimeField(null=True, blank=True)
    resolution_time = models.DateTimeField(null=True, blank=True)
    
    # Escalation
    escalation_level = models.IntegerField(default=0)
    escalated_at = models.DateTimeField(null=True, blank=True)
    escalated_to = models.ForeignKey(
        BaseUserModel, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='escalated_tickets'
    )
    
    # Resolution
    resolution = models.TextField(blank=True, null=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(
        BaseUserModel, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='resolved_tickets'
    )
    closed_at = models.DateTimeField(null=True, blank=True)
    closed_by = models.ForeignKey(
        BaseUserModel, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='closed_tickets'
    )
    
    # Attachments
    attachments = models.JSONField(default=list, blank=True)
    tags = models.JSONField(default=list, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'priority']),
            models.Index(fields=['assigned_to', 'status']),
            models.Index(fields=['sla_deadline', 'sla_status']),
        ]
    
    def __str__(self):
        return f"{self.ticket_number} - {self.title}"


class TicketComment(models.Model):
    """Ticket Comments/Updates"""
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    ticket = models.ForeignKey(
        Ticket, on_delete=models.CASCADE,
        related_name='comments'
    )
    user = models.ForeignKey(
        BaseUserModel, on_delete=models.CASCADE,
        related_name='ticket_comments'
    )
    comment = models.TextField()
    is_internal = models.BooleanField(default=False, help_text="Internal note not visible to customer")
    attachments = models.JSONField(default=list, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"Comment on {self.ticket.ticket_number}"


class TicketAssignmentRule(models.Model):
    """Auto Assignment Rules"""
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    organization = models.ForeignKey(
        BaseUserModel, on_delete=models.CASCADE,
        limit_choices_to={'role': 'organization'},
        related_name='org_ticket_assignment_rules'
    )
    
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    priority = models.CharField(
        max_length=20,
        choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High'), ('critical', 'Critical')],
        null=True, blank=True
    )
    category = models.ForeignKey(
        TicketCategory, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='assignment_rules'
    )
    
    # Assignment Logic
    assign_to_user = models.ForeignKey(
        BaseUserModel, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='assigned_ticket_rules',
        limit_choices_to={'role__in': ['admin', 'user']}
    )
    assign_to_department = models.CharField(max_length=255, blank=True, null=True)
    round_robin = models.BooleanField(default=False, help_text="Assign in round-robin fashion")
    
    # Conditions
    conditions = models.JSONField(default=dict, blank=True, help_text="JSON conditions for matching")
    is_active = models.BooleanField(default=True)
    priority_order = models.IntegerField(default=0, help_text="Higher number = higher priority")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-priority_order', 'name']
    
    def __str__(self):
        return self.name


class SLAPolicy(models.Model):
    """SLA Policies"""
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    organization = models.ForeignKey(
        BaseUserModel, on_delete=models.CASCADE,
        limit_choices_to={'role': 'organization'},
        related_name='sla_policies'
    )
    
    name = models.CharField(max_length=255)
    category = models.ForeignKey(
        TicketCategory, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='sla_policies'
    )
    priority = models.CharField(
        max_length=20,
        choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High'), ('critical', 'Critical')],
        null=True, blank=True
    )
    
    # SLA Times (in hours)
    first_response_time = models.IntegerField(default=4, help_text="First response time in hours")
    resolution_time = models.IntegerField(default=24, help_text="Resolution time in hours")
    
    # Escalation
    escalation_enabled = models.BooleanField(default=True)
    escalation_time = models.IntegerField(default=12, help_text="Escalate after X hours")
    escalation_to = models.ForeignKey(
        BaseUserModel, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='escalation_policies'
    )
    
    # Business Hours
    business_hours_only = models.BooleanField(default=False)
    business_hours_start = models.TimeField(null=True, blank=True)
    business_hours_end = models.TimeField(null=True, blank=True)
    business_days = models.JSONField(default=list, blank=True, help_text="Days of week [0-6]")
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name


class TicketEscalationLog(models.Model):
    """Ticket Escalation History"""
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    ticket = models.ForeignKey(
        Ticket, on_delete=models.CASCADE,
        related_name='escalation_logs'
    )
    escalation_level = models.IntegerField()
    escalated_from = models.ForeignKey(
        BaseUserModel, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='escalated_from_tickets'
    )
    escalated_to = models.ForeignKey(
        BaseUserModel, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='escalated_to_tickets'
    )
    reason = models.TextField(blank=True, null=True)
    escalated_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-escalated_at']
    
    def __str__(self):
        return f"Escalation {self.escalation_level} - {self.ticket.ticket_number}"

