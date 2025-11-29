"""
Comprehensive Advanced Leave Management System for India
Covers all leave types, policies, accrual, encashment, comp-off, etc.
"""

from django.db import models
from django.db.models import Q
from uuid import uuid4
from decimal import Decimal
from datetime import date, datetime, timedelta
from AuthN.models import *


# ==================== LEAVE TYPE ====================
class LeaveType(models.Model):
    """Leave Type Master - Extended with Indian leave types"""
    id = models.BigAutoField(primary_key=True)
    admin = models.ForeignKey(
        BaseUserModel, on_delete=models.CASCADE,
        limit_choices_to={'role': 'admin'},
        related_name='admin_leave_types'
    )
    organization = models.ForeignKey(
        BaseUserModel, on_delete=models.CASCADE,
        limit_choices_to={'role': 'organization'},
        related_name='organization_leave_policies'
    )
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20)  # CL, SL, EL, PL, ML, etc.
    
    # Leave Type Classification
    LEAVE_CATEGORY_CHOICES = [
        ('casual', 'Casual Leave (CL)'),
        ('sick', 'Sick Leave (SL)'),
        ('earned', 'Earned Leave (EL)'),
        ('privilege', 'Privilege Leave (PL)'),
        ('maternity', 'Maternity Leave (ML)'),
        ('paternity', 'Paternity Leave'),
        ('compensatory', 'Compensatory Off (Comp Off)'),
        ('lwp', 'Leave Without Pay (LWP)'),
        ('sabbatical', 'Sabbatical Leave'),
        ('bereavement', 'Bereavement Leave'),
        ('marriage', 'Marriage Leave'),
        ('other', 'Other')
    ]
    category = models.CharField(max_length=20, choices=LEAVE_CATEGORY_CHOICES, default='other')
    
    # Basic Settings
    default_count = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    max_count = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    is_paid = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    
    # Accrual Settings
    accrual_enabled = models.BooleanField(default=False)
    accrual_frequency = models.CharField(
        max_length=20,
        choices=[('monthly', 'Monthly'), ('quarterly', 'Quarterly'), ('yearly', 'Yearly')],
        default='monthly'
    )
    accrual_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, help_text="Days per accrual period")
    
    # Carry Forward Settings
    carry_forward_enabled = models.BooleanField(default=False)
    max_carry_forward = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    carry_forward_validity_months = models.IntegerField(default=12, help_text="Months after which carry forward expires")
    
    # Encashment Settings
    encashment_enabled = models.BooleanField(default=False)
    max_encashment_days = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    encashment_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=100.00, help_text="% of salary for encashment")
    
    # Approval Settings
    requires_approval = models.BooleanField(default=True)
    min_advance_days = models.IntegerField(default=0, help_text="Minimum days in advance for application")
    max_consecutive_days = models.IntegerField(null=True, blank=True, help_text="Maximum consecutive days allowed")
    
    # Half Day Settings
    half_day_allowed = models.BooleanField(default=False)
    short_leave_allowed = models.BooleanField(default=False)
    short_leave_duration_hours = models.DecimalField(max_digits=4, decimal_places=2, default=2.00)
    
    # Other Settings
    requires_medical_certificate = models.BooleanField(default=False)
    requires_document = models.BooleanField(default=False)
    description = models.TextField(blank=True, null=True)
    color_code = models.CharField(max_length=7, default='#3498db', help_text="Hex color for calendar display")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('admin', 'code', 'is_active')
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.code})"


# ==================== LEAVE POLICY ====================
class LeavePolicy(models.Model):
    """Leave Policy - Organization/Department/Designation level"""
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    organization = models.ForeignKey(
        BaseUserModel, on_delete=models.CASCADE,
        limit_choices_to={'role': 'organization'},
        related_name='leave_policies'
    )
    admin = models.ForeignKey(
        BaseUserModel, on_delete=models.CASCADE,
        limit_choices_to={'role': 'admin'},
        related_name='admin_leave_policies',
        null=True, blank=True
    )
    
    # Policy Scope
    POLICY_SCOPE_CHOICES = [
        ('organization', 'Organization Wide'),
        ('department', 'Department'),
        ('designation', 'Designation'),
        ('employee', 'Individual Employee')
    ]
    scope = models.CharField(max_length=20, choices=POLICY_SCOPE_CHOICES, default='organization')
    scope_value = models.CharField(max_length=200, null=True, blank=True, help_text="Department/Designation/Employee ID")
    
    # Policy Details
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    effective_from = models.DateField()
    effective_to = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    # Leave Allocations (JSON)
    leave_allocations = models.JSONField(
        default=dict,
        help_text="{'CL': 12, 'SL': 12, 'EL': 15, ...}"
    )
    
    # Rules
    probation_period_days = models.IntegerField(default=90, help_text="Days before leave can be availed")
    max_leaves_per_month = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    weekend_count_in_leave = models.BooleanField(default=False)
    holiday_count_in_leave = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        BaseUserModel, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='created_leave_policies'
    )
    
    class Meta:
        ordering = ['-effective_from', 'name']
    
    def __str__(self):
        return f"{self.name} - {self.scope}"


# ==================== EMPLOYEE LEAVE BALANCE ====================
class EmployeeLeaveBalance(models.Model):
    """Employee Leave Balance - Extended"""
    id = models.BigAutoField(primary_key=True)
    admin = models.ForeignKey(
        BaseUserModel, on_delete=models.CASCADE,
        limit_choices_to={'role': 'admin'},
        related_name='admin_leave_balances'
    )
    user = models.ForeignKey(
        BaseUserModel, on_delete=models.CASCADE,
        limit_choices_to={'role': 'user'},
        related_name='user_leave_balances'
    )
    leave_type = models.ForeignKey(LeaveType, on_delete=models.CASCADE, related_name='employee_balances')
    year = models.PositiveIntegerField()
    
    # Balance Details
    opening_balance = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    accrued = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    assigned = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    used = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    pending = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    cancelled = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    carried_forward = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    encashed = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    lapsed = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    
    # Carry Forward Details
    carry_forward_from_previous = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    carry_forward_to_next = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    carry_forward_expiry_date = models.DateField(null=True, blank=True)
    
    is_active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_accrued_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ('user', 'leave_type', 'year', 'is_active')
        ordering = ['-year', 'leave_type__name']
        indexes = [
            models.Index(fields=['user', 'year']),
            models.Index(fields=['leave_type', 'year']),
        ]
    
    @property
    def total_available(self):
        """Total available leaves"""
        return self.assigned + self.carried_forward - self.used - self.pending
    
    @property
    def balance(self):
        """Current balance"""
        return self.total_available
    
    @property
    def closing_balance(self):
        """Closing balance for the year"""
        return self.assigned + self.carried_forward - self.used - self.encashed - self.lapsed
    
    def __str__(self):
        return f"{self.user.email} - {self.leave_type.code} ({self.year}): {self.balance} days"


# ==================== LEAVE APPLICATION ====================
class LeaveApplication(models.Model):
    """Leave Application - Extended with advanced features"""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
        ('partially_approved', 'Partially Approved')
    ]
    
    LEAVE_DURATION_CHOICES = [
        ('full_day', 'Full Day'),
        ('half_day', 'Half Day'),
        ('short_leave', 'Short Leave'),
        ('multiple_days', 'Multiple Days')
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
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
    from_time = models.TimeField(null=True, blank=True, help_text="For half day/short leave")
    to_time = models.TimeField(null=True, blank=True, help_text="For half day/short leave")
    duration_type = models.CharField(max_length=20, choices=LEAVE_DURATION_CHOICES, default='full_day')
    total_days = models.DecimalField(max_digits=5, decimal_places=2)
    
    # Application Details
    reason = models.TextField()
    contact_number = models.CharField(max_length=20, blank=True, null=True)
    alternate_contact = models.CharField(max_length=20, blank=True, null=True)
    
    # Documents
    medical_certificate = models.FileField(upload_to='leave_documents/', blank=True, null=True)
    supporting_documents = models.JSONField(default=list, blank=True, help_text="List of document URLs")
    
    # Status & Approval
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    applied_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(blank=True, null=True)
    reviewed_by = models.ForeignKey(
        BaseUserModel, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='reviewed_leaves'
    )
    comments = models.TextField(blank=True, null=True)
    rejection_reason = models.TextField(blank=True, null=True)
    
    # Workflow
    current_approver = models.ForeignKey(
        BaseUserModel, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='pending_leave_approvals',
        limit_choices_to={'role__in': ['admin', 'user']}
    )
    approval_workflow = models.JSONField(
        default=list,
        help_text="[{'approver_id': '...', 'status': 'pending', 'approved_at': '...'}]"
    )
    
    # Balance Tracking
    balance_before = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    balance_after = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    # Cancellation
    cancelled_at = models.DateTimeField(null=True, blank=True)
    cancelled_by = models.ForeignKey(
        BaseUserModel, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='cancelled_leaves'
    )
    cancellation_reason = models.TextField(blank=True, null=True)
    
    # Modification
    is_modified = models.BooleanField(default=False)
    modified_from = models.JSONField(null=True, blank=True, help_text="Previous leave details")
    modified_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-applied_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['from_date', 'to_date']),
            models.Index(fields=['leave_type', 'status']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.leave_type.code} ({self.from_date} to {self.to_date})"


# ==================== COMPENSATORY OFF ====================
class CompensatoryOff(models.Model):
    """Compensatory Off Management"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('used', 'Used'),
        ('expired', 'Expired')
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    admin = models.ForeignKey(
        BaseUserModel, on_delete=models.CASCADE,
        limit_choices_to={'role': 'admin'},
        related_name='admin_comp_offs'
    )
    user = models.ForeignKey(
        BaseUserModel, on_delete=models.CASCADE,
        limit_choices_to={'role': 'user'},
        related_name='user_comp_offs'
    )
    
    # Comp Off Details
    work_date = models.DateField(help_text="Date when extra work was done")
    work_start_time = models.TimeField()
    work_end_time = models.TimeField()
    total_hours = models.DecimalField(max_digits=5, decimal_places=2)
    comp_off_days = models.DecimalField(max_digits=5, decimal_places=2, default=1.00)
    
    # Approval
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    approved_by = models.ForeignKey(
        BaseUserModel, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='approved_comp_offs'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    comments = models.TextField(blank=True, null=True)
    
    # Usage
    used_in_leave = models.ForeignKey(
        LeaveApplication, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='comp_off_used'
    )
    used_at = models.DateTimeField(null=True, blank=True)
    
    # Expiry
    expiry_date = models.DateField(null=True, blank=True)
    is_expired = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-work_date']
    
    def __str__(self):
        return f"{self.user.email} - Comp Off ({self.work_date})"


# ==================== LEAVE ENCASHMENT ====================
class LeaveEncashment(models.Model):
    """Leave Encashment Management"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('processed', 'Processed')
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    admin = models.ForeignKey(
        BaseUserModel, on_delete=models.CASCADE,
        limit_choices_to={'role': 'admin'},
        related_name='admin_leave_encashments'
    )
    user = models.ForeignKey(
        BaseUserModel, on_delete=models.CASCADE,
        limit_choices_to={'role': 'user'},
        related_name='user_leave_encashments'
    )
    leave_type = models.ForeignKey(LeaveType, on_delete=models.PROTECT)
    leave_balance = models.ForeignKey(EmployeeLeaveBalance, on_delete=models.PROTECT)
    
    # Encashment Details
    encashment_date = models.DateField()
    days_to_encash = models.DecimalField(max_digits=5, decimal_places=2)
    encashment_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=100.00)
    daily_rate = models.DecimalField(max_digits=12, decimal_places=2)
    encashment_amount = models.DecimalField(max_digits=12, decimal_places=2)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    reason = models.TextField()
    approved_by = models.ForeignKey(
        BaseUserModel, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='approved_encashments'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    comments = models.TextField(blank=True, null=True)
    
    # Payroll Integration
    payroll_month = models.IntegerField(null=True, blank=True)
    payroll_year = models.IntegerField(null=True, blank=True)
    payroll_record = models.ForeignKey(
        'PayrollSystem.PayrollRecord',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='leave_encashments'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-encashment_date']
    
    def __str__(self):
        return f"{self.user.email} - Encashment ({self.days_to_encash} days)"


# ==================== LEAVE BALANCE ADJUSTMENT ====================
class LeaveBalanceAdjustment(models.Model):
    """Manual Leave Balance Adjustments"""
    ADJUSTMENT_TYPE_CHOICES = [
        ('credit', 'Credit'),
        ('debit', 'Debit'),
        ('correction', 'Correction')
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    admin = models.ForeignKey(
        BaseUserModel, on_delete=models.CASCADE,
        limit_choices_to={'role': 'admin'},
        related_name='admin_leave_adjustments'
    )
    user = models.ForeignKey(
        BaseUserModel, on_delete=models.CASCADE,
        limit_choices_to={'role': 'user'},
        related_name='user_leave_adjustments'
    )
    leave_type = models.ForeignKey(LeaveType, on_delete=models.PROTECT)
    leave_balance = models.ForeignKey(EmployeeLeaveBalance, on_delete=models.PROTECT)
    
    # Adjustment Details
    adjustment_date = models.DateField()
    adjustment_type = models.CharField(max_length=20, choices=ADJUSTMENT_TYPE_CHOICES)
    days = models.DecimalField(max_digits=5, decimal_places=2)
    balance_before = models.DecimalField(max_digits=5, decimal_places=2)
    balance_after = models.DecimalField(max_digits=5, decimal_places=2)
    
    # Details
    reason = models.TextField()
    reference_number = models.CharField(max_length=100, blank=True, null=True)
    approved_by = models.ForeignKey(
        BaseUserModel, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='approved_adjustments'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        BaseUserModel, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='created_adjustments'
    )
    
    class Meta:
        ordering = ['-adjustment_date']
    
    def __str__(self):
        return f"{self.user.email} - {self.adjustment_type} ({self.days} days)"


# ==================== LEAVE ACCRUAL LOG ====================
class LeaveAccrualLog(models.Model):
    """Log of Leave Accruals"""
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    user = models.ForeignKey(
        BaseUserModel, on_delete=models.CASCADE,
        limit_choices_to={'role': 'user'},
        related_name='leave_accrual_logs'
    )
    leave_type = models.ForeignKey(LeaveType, on_delete=models.CASCADE)
    leave_balance = models.ForeignKey(EmployeeLeaveBalance, on_delete=models.CASCADE)
    
    # Accrual Details
    accrual_date = models.DateField()
    accrual_period_start = models.DateField()
    accrual_period_end = models.DateField()
    days_accrued = models.DecimalField(max_digits=5, decimal_places=2)
    balance_before = models.DecimalField(max_digits=5, decimal_places=2)
    balance_after = models.DecimalField(max_digits=5, decimal_places=2)
    
    # Status
    is_processed = models.BooleanField(default=False)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-accrual_date']
        indexes = [
            models.Index(fields=['user', 'accrual_date']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.leave_type.code} ({self.days_accrued} days)"


# ==================== LEAVE APPROVAL DELEGATION ====================
class LeaveApprovalDelegation(models.Model):
    """Leave Approval Delegation"""
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    delegator = models.ForeignKey(
        BaseUserModel, on_delete=models.CASCADE,
        limit_choices_to={'role__in': ['admin', 'user']},
        related_name='delegated_approvals'
    )
    delegate = models.ForeignKey(
        BaseUserModel, on_delete=models.CASCADE,
        limit_choices_to={'role__in': ['admin', 'user']},
        related_name='received_delegations'
    )
    organization = models.ForeignKey(
        BaseUserModel, on_delete=models.CASCADE,
        limit_choices_to={'role': 'organization'}
    )
    
    # Delegation Details
    effective_from = models.DateField()
    effective_to = models.DateField()
    is_active = models.BooleanField(default=True)
    
    # Scope
    leave_types = models.ManyToManyField(LeaveType, blank=True, help_text="Leave types for delegation (empty = all)")
    max_approval_amount = models.DecimalField(
        max_digits=5, decimal_places=2,
        null=True, blank=True,
        help_text="Maximum days that can be approved"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-effective_from']
    
    def __str__(self):
        return f"{self.delegator.email} -> {self.delegate.email}"


# ==================== LEAVE CALENDAR EVENT ====================
class LeaveCalendarEvent(models.Model):
    """Leave Calendar Events for visualization"""
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    leave_application = models.OneToOneField(
        LeaveApplication, on_delete=models.CASCADE,
        related_name='calendar_event'
    )
    user = models.ForeignKey(
        BaseUserModel, on_delete=models.CASCADE,
        limit_choices_to={'role': 'user'}
    )
    
    # Event Details
    event_date = models.DateField()
    is_full_day = models.BooleanField(default=True)
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    
    # Display
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    color = models.CharField(max_length=7, default='#3498db')
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['event_date']
        indexes = [
            models.Index(fields=['user', 'event_date']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.event_date}"
