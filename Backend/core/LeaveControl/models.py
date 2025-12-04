"""
Simple Leave Management System
"""

from django.db import models
from datetime import datetime
from decimal import Decimal
from AuthN.models import *


# ==================== LEAVE TYPE ====================
class LeaveType(models.Model):
    """Leave Type Master"""
    id = models.BigAutoField(primary_key=True)
    admin = models.ForeignKey(
        BaseUserModel, on_delete=models.CASCADE,
        limit_choices_to={'role': 'admin'},
        related_name='admin_leave_types'
    )
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20)  # CL, SL, EL, PL, ML, etc.
    description = models.TextField(blank=True, null=True)
    
    # Leave Settings
    default_count = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    is_paid = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('admin', 'code', 'is_active')
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.code})"


# ==================== EMPLOYEE LEAVE BALANCE ====================
class EmployeeLeaveBalance(models.Model):
    """Employee Leave Balance - One user can have multiple leave types"""
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(
        BaseUserModel, on_delete=models.CASCADE,
        limit_choices_to={'role': 'user'},
        related_name='leave_balances'
    )
    leave_type = models.ForeignKey(LeaveType, on_delete=models.CASCADE, related_name='employee_balances')
    year = models.PositiveIntegerField()
    
    # Balance Details
    assigned = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    used = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('user', 'leave_type', 'year')
        ordering = ['-year', 'leave_type__name']
        indexes = [
            models.Index(fields=['user', 'year']),
            models.Index(fields=['leave_type', 'year']),
        ]
    
    @property
    def balance(self):
        """Current balance - Returns Decimal"""
        assigned = self.assigned if isinstance(self.assigned, Decimal) else Decimal(str(self.assigned))
        used = self.used if isinstance(self.used, Decimal) else Decimal(str(self.used))
        return assigned - used
    
    def __str__(self):
        return f"{self.user.email} - {self.leave_type.code} ({self.year}): {self.balance} days"


# ==================== LEAVE APPLICATION ====================
class LeaveApplication(models.Model):
    """Leave Application"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    ]
    
    id = models.BigAutoField(primary_key=True)
    admin = models.ForeignKey(
        BaseUserModel, on_delete=models.CASCADE,
        limit_choices_to={'role': 'admin'},
        related_name='admin_leave_applications'
    )
    organization = models.ForeignKey(
        BaseUserModel, on_delete=models.CASCADE,
        limit_choices_to={'role': 'organization'},
        related_name='org_leave_applications'
    )
    user = models.ForeignKey(
        BaseUserModel, on_delete=models.CASCADE,
        limit_choices_to={'role': 'user'},
        related_name='user_leave_applications'
    )
    leave_type = models.ForeignKey(LeaveType, on_delete=models.PROTECT, related_name='applications')
    
    # Leave Details
    from_date = models.DateField()
    to_date = models.DateField()
    total_days = models.DecimalField(max_digits=5, decimal_places=2)
    reason = models.TextField()
    
    # Status & Approval
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    applied_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(blank=True, null=True)
    reviewed_by = models.ForeignKey(
        BaseUserModel, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='reviewed_leaves'
    )
    comments = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-applied_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['from_date', 'to_date']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.leave_type.code} ({self.from_date} to {self.to_date})"
