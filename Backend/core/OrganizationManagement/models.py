"""
Organization Management System
Subscription plans, expiry management, module management, super admin features
"""

from django.db import models
from uuid import uuid4
from decimal import Decimal
from datetime import date, datetime, timedelta
from AuthN.models import *


class SubscriptionPlan(models.Model):
    """Subscription Plans"""
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True, null=True)
    
    # Pricing
    price = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=10, default='INR')
    billing_cycle = models.CharField(
        max_length=20,
        choices=[('monthly', 'Monthly'), ('quarterly', 'Quarterly'), ('yearly', 'Yearly')],
        default='monthly'
    )
    
    # Limits
    max_employees = models.IntegerField(default=10)
    max_storage_gb = models.IntegerField(default=5)
    max_api_calls_per_day = models.IntegerField(default=1000)
    
    # Features
    enabled_modules = models.JSONField(
        default=list,
        blank=True,
        help_text="List of enabled module codes"
    )
    
    # Grace Period
    grace_period_days = models.IntegerField(default=7, help_text="Grace period after expiry")
    
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['price']
    
    def __str__(self):
        return f"{self.name} - ₹{self.price}/{self.billing_cycle}"


class OrganizationSubscription(models.Model):
    """Organization Subscriptions"""
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('suspended', 'Suspended'),
        ('cancelled', 'Cancelled'),
        ('trial', 'Trial')
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    organization = models.OneToOneField(
        BaseUserModel, on_delete=models.CASCADE,
        limit_choices_to={'role': 'organization'},
        related_name='subscription'
    )
    plan = models.ForeignKey(
        SubscriptionPlan, on_delete=models.PROTECT,
        related_name='subscriptions'
    )
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='trial')
    
    # Dates
    start_date = models.DateField()
    expiry_date = models.DateField()
    grace_period_end = models.DateField(null=True, blank=True)
    
    # Payment
    payment_status = models.CharField(
        max_length=20,
        choices=[('paid', 'Paid'), ('pending', 'Pending'), ('failed', 'Failed')],
        default='pending'
    )
    last_payment_date = models.DateField(null=True, blank=True)
    next_payment_date = models.DateField(null=True, blank=True)
    
    # Renewal
    auto_renewal = models.BooleanField(default=False)
    renewal_reminder_sent = models.BooleanField(default=False)
    
    # Custom Limits (overrides plan limits)
    custom_max_employees = models.IntegerField(null=True, blank=True)
    custom_max_storage_gb = models.IntegerField(null=True, blank=True)
    custom_max_api_calls = models.IntegerField(null=True, blank=True)
    
    # Custom Modules
    custom_enabled_modules = models.JSONField(default=list, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-expiry_date']
    
    def __str__(self):
        return f"{self.organization.email} - {self.plan.name} - {self.status}"
    
    @property
    def is_expired(self):
        return date.today() > self.expiry_date
    
    @property
    def is_in_grace_period(self):
        if self.grace_period_end:
            return date.today() <= self.grace_period_end
        return False


class OrganizationModule(models.Model):
    """Organization Module Access Control"""
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    organization = models.ForeignKey(
        BaseUserModel, on_delete=models.CASCADE,
        limit_choices_to={'role': 'organization'},
        related_name='module_access'
    )
    
    module_code = models.CharField(max_length=100)
    module_name = models.CharField(max_length=255)
    is_enabled = models.BooleanField(default=True)
    enabled_at = models.DateTimeField(null=True, blank=True)
    disabled_at = models.DateTimeField(null=True, blank=True)
    
    # Limits (module-specific)
    limits = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('organization', 'module_code')
        ordering = ['module_name']
    
    def __str__(self):
        return f"{self.organization.email} - {self.module_name}"


class OrganizationUsage(models.Model):
    """Organization Usage Statistics"""
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    organization = models.ForeignKey(
        BaseUserModel, on_delete=models.CASCADE,
        limit_choices_to={'role': 'organization'},
        related_name='usage_stats'
    )
    
    # Period
    period_type = models.CharField(
        max_length=20,
        choices=[('daily', 'Daily'), ('monthly', 'Monthly'), ('yearly', 'Yearly')],
        default='monthly'
    )
    period_start = models.DateField()
    period_end = models.DateField()
    
    # Usage Metrics
    employee_count = models.IntegerField(default=0)
    storage_used_gb = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    api_calls_count = models.IntegerField(default=0)
    
    # Feature Usage
    attendance_records = models.IntegerField(default=0)
    payroll_runs = models.IntegerField(default=0)
    leave_applications = models.IntegerField(default=0)
    expense_submissions = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('organization', 'period_type', 'period_start')
        ordering = ['-period_start']
    
    def __str__(self):
        return f"{self.organization.email} - {self.period_start} to {self.period_end}"


class OrganizationDeactivationLog(models.Model):
    """Organization Deactivation History"""
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    organization = models.ForeignKey(
        BaseUserModel, on_delete=models.CASCADE,
        limit_choices_to={'role': 'organization'},
        related_name='deactivation_logs'
    )
    
    # Deactivation Details
    reason = models.CharField(
        max_length=50,
        choices=[
            ('payment_failed', 'Payment Failed'),
            ('plan_expired', 'Plan Expired'),
            ('policy_violation', 'Policy Violation'),
            ('manual_suspend', 'Manual Suspend'),
            ('trial_expired', 'Trial Expired'),
            ('other', 'Other')
        ]
    )
    reason_description = models.TextField(blank=True, null=True)
    
    # Actions
    deactivated_by = models.ForeignKey(
        BaseUserModel, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='deactivated_organizations'
    )
    deactivated_at = models.DateTimeField(auto_now_add=True)
    
    # Reactivation
    reactivated_at = models.DateTimeField(null=True, blank=True)
    reactivated_by = models.ForeignKey(
        BaseUserModel, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='reactivated_organizations'
    )
    
    class Meta:
        ordering = ['-deactivated_at']
    
    def __str__(self):
        return f"{self.organization.email} - {self.reason} - {self.deactivated_at}"


class SuperAdminAction(models.Model):
    """Super Admin Actions Log"""
    ACTION_TYPES = [
        ('org_create', 'Create Organization'),
        ('org_activate', 'Activate Organization'),
        ('org_deactivate', 'Deactivate Organization'),
        ('org_delete', 'Delete Organization'),
        ('plan_assign', 'Assign Plan'),
        ('module_enable', 'Enable Module'),
        ('module_disable', 'Disable Module'),
        ('limit_increase', 'Increase Limit'),
        ('force_logout', 'Force Logout'),
        ('data_export', 'Data Export'),
        ('other', 'Other')
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    super_admin = models.ForeignKey(
        BaseUserModel, on_delete=models.SET_NULL,
        null=True, blank=True,
        limit_choices_to={'role': 'system_owner'},
        related_name='super_admin_actions'
    )
    organization = models.ForeignKey(
        BaseUserModel, on_delete=models.SET_NULL,
        null=True, blank=True,
        limit_choices_to={'role': 'organization'},
        related_name='admin_actions'
    )
    
    action_type = models.CharField(max_length=50, choices=ACTION_TYPES)
    description = models.TextField()
    details = models.JSONField(default=dict, blank=True)
    
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.action_type} - {self.organization.email if self.organization else 'N/A'} - {self.created_at}"

