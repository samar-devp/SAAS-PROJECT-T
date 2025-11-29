"""
Advanced Expense Management System for India
Comprehensive expense tracking, approval, reimbursement, and tax compliance
"""

from django.db import models
from uuid import uuid4
from decimal import Decimal
from datetime import date, datetime
from AuthN.models import *


class ExpenseCategory(models.Model):
    """Expense Category - Extended"""
    id = models.BigAutoField(primary_key=True)
    admin = models.ForeignKey(
        BaseUserModel, on_delete=models.CASCADE,
        limit_choices_to={'role': 'admin'},
        related_name="admin_expense_categories"
    )
    organization = models.ForeignKey(
        BaseUserModel, on_delete=models.CASCADE,
        limit_choices_to={'role': 'organization'},
        related_name="organization_expense_categories"
    )
    name = models.CharField(max_length=255, default="Service Expense")
    description = models.TextField(blank=True, null=True)
    code = models.CharField(max_length=50, blank=True, null=True)
    
    # Tax Settings
    is_taxable = models.BooleanField(default=True)
    gst_applicable = models.BooleanField(default=True)
    gst_rate = models.DecimalField(max_digits=5, decimal_places=2, default=18.00, help_text="GST %")
    tds_applicable = models.BooleanField(default=False)
    tds_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, help_text="TDS %")
    
    # Limits
    max_amount_per_transaction = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    max_amount_per_month = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    requires_approval = models.BooleanField(default=True)
    requires_receipt = models.BooleanField(default=True)
    
    # Budget
    monthly_budget = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    
    color_code = models.CharField(max_length=7, default='#3498db')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('organization', 'code') if 'code' else None
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Expense(models.Model):
    """Expense Model - Advanced"""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('reimbursed', 'Reimbursed'),
        ('cancelled', 'Cancelled')
    ]
    
    PAYMENT_MODE_CHOICES = [
        ('cash', 'Cash'),
        ('card', 'Card'),
        ('upi', 'UPI'),
        ('netbanking', 'Net Banking'),
        ('cheque', 'Cheque'),
        ('neft', 'NEFT'),
        ('rtgs', 'RTGS'),
        ('other', 'Other')
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    admin = models.ForeignKey(
        BaseUserModel, on_delete=models.CASCADE,
        limit_choices_to={'role': 'admin'},
        related_name='admin_expenses'
    )
    organization = models.ForeignKey(
        BaseUserModel, on_delete=models.CASCADE,
        limit_choices_to={'role': 'organization'},
        related_name='org_expenses'
    )
    employee = models.ForeignKey(
        BaseUserModel, on_delete=models.CASCADE,
        limit_choices_to={'role': 'user'},
        related_name='employee_expenses'
    )
    category = models.ForeignKey(
        ExpenseCategory, on_delete=models.PROTECT,
        related_name='expenses'
    )
    
    # Expense Details
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    expense_date = models.DateField()
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default='INR')
    
    # Tax Details
    gst_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    tds_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    amount_before_tax = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    
    # Payment Details
    payment_mode = models.CharField(max_length=20, choices=PAYMENT_MODE_CHOICES, default='cash')
    payment_reference = models.CharField(max_length=100, blank=True, null=True)
    vendor_name = models.CharField(max_length=255, blank=True, null=True)
    vendor_gstin = models.CharField(max_length=15, blank=True, null=True)
    invoice_number = models.CharField(max_length=100, blank=True, null=True)
    invoice_date = models.DateField(null=True, blank=True)
    
    # Location
    location = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    
    # Status & Approval
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    submitted_at = models.DateTimeField(null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(
        BaseUserModel, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='approved_expenses',
        limit_choices_to={'role__in': ['admin', 'user']}
    )
    rejection_reason = models.TextField(blank=True, null=True)
    rejected_at = models.DateTimeField(null=True, blank=True)
    rejected_by = models.ForeignKey(
        BaseUserModel, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='rejected_expenses'
    )
    
    # Reimbursement
    reimbursement_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    reimbursement_date = models.DateField(null=True, blank=True)
    reimbursement_mode = models.CharField(max_length=20, choices=PAYMENT_MODE_CHOICES, blank=True, null=True)
    reimbursement_reference = models.CharField(max_length=100, blank=True, null=True)
    
    # Documents
    receipts = models.JSONField(default=list, blank=True, help_text="List of receipt file paths")
    supporting_documents = models.JSONField(default=list, blank=True)
    
    # Mileage/Travel
    is_travel_expense = models.BooleanField(default=False)
    distance_km = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    rate_per_km = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    from_location = models.CharField(max_length=255, blank=True, null=True)
    to_location = models.CharField(max_length=255, blank=True, null=True)
    
    # Project/Task Association
    project = models.ForeignKey(
        'TaskControl.Project',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='expenses'
    )
    task = models.ForeignKey(
        'TaskControl.Task',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='expenses'
    )
    
    # Additional
    tags = models.JSONField(default=list, blank=True)
    remarks = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        BaseUserModel, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='created_expenses'
    )
    
    class Meta:
        ordering = ['-expense_date', '-created_at']
        indexes = [
            models.Index(fields=['employee', 'status']),
            models.Index(fields=['expense_date', 'status']),
            models.Index(fields=['category', 'status']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.employee.email} - ₹{self.total_amount}"


class ExpensePolicy(models.Model):
    """Expense Policy - Organization level"""
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    organization = models.ForeignKey(
        BaseUserModel, on_delete=models.CASCADE,
        limit_choices_to={'role': 'organization'},
        related_name='expense_policies'
    )
    admin = models.ForeignKey(
        BaseUserModel, on_delete=models.CASCADE,
        limit_choices_to={'role': 'admin'},
        related_name='admin_expense_policies',
        null=True, blank=True
    )
    
    # Policy Details
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    effective_from = models.DateField()
    effective_to = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    # Limits
    max_expense_per_day = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    max_expense_per_month = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    max_expense_per_transaction = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    
    # Approval Rules
    auto_approve_below = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    requires_manager_approval_above = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    requires_finance_approval_above = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    
    # Submission Rules
    submission_deadline_days = models.IntegerField(default=30, help_text="Days after expense date to submit")
    requires_receipt_above = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    
    # Reimbursement Rules
    reimbursement_cycle = models.CharField(
        max_length=20,
        choices=[('weekly', 'Weekly'), ('biweekly', 'Bi-Weekly'), ('monthly', 'Monthly')],
        default='monthly'
    )
    reimbursement_day = models.IntegerField(default=1, help_text="Day of month/week for reimbursement")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        BaseUserModel, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='created_expense_policies'
    )
    
    class Meta:
        ordering = ['-effective_from']
    
    def __str__(self):
        return f"{self.name} - {self.organization.email}"


class ExpenseApprovalWorkflow(models.Model):
    """Expense Approval Workflow"""
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    expense = models.ForeignKey(
        Expense, on_delete=models.CASCADE,
        related_name='approval_workflow'
    )
    
    approver = models.ForeignKey(
        BaseUserModel, on_delete=models.CASCADE,
        related_name='expense_approvals'
    )
    level = models.IntegerField(default=1, help_text="Approval level (1, 2, 3...)")
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected'),
            ('skipped', 'Skipped')
        ],
        default='pending'
    )
    comments = models.TextField(blank=True, null=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['level', 'created_at']
        unique_together = ('expense', 'approver', 'level')
    
    def __str__(self):
        return f"{self.expense.title} - Level {self.level} - {self.approver.email}"


class ExpenseReimbursement(models.Model):
    """Expense Reimbursement Batch"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('processed', 'Processed'),
        ('paid', 'Paid'),
        ('failed', 'Failed')
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    organization = models.ForeignKey(
        BaseUserModel, on_delete=models.CASCADE,
        limit_choices_to={'role': 'organization'}
    )
    employee = models.ForeignKey(
        BaseUserModel, on_delete=models.CASCADE,
        limit_choices_to={'role': 'user'},
        related_name='expense_reimbursements'
    )
    
    # Reimbursement Details
    reimbursement_date = models.DateField()
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    expenses = models.ManyToManyField(Expense, related_name='reimbursements')
    
    # Payment
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_mode = models.CharField(max_length=20, default='neft')
    payment_reference = models.CharField(max_length=100, blank=True, null=True)
    payment_date = models.DateField(null=True, blank=True)
    processed_by = models.ForeignKey(
        BaseUserModel, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='processed_reimbursements'
    )
    
    # Payroll Integration
    payroll_month = models.IntegerField(null=True, blank=True)
    payroll_year = models.IntegerField(null=True, blank=True)
    payroll_record = models.ForeignKey(
        'PayrollSystem.PayrollRecord',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='expense_reimbursements'
    )
    
    remarks = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-reimbursement_date']
    
    def __str__(self):
        return f"Reimbursement - {self.employee.email} - ₹{self.total_amount}"


class ExpenseBudget(models.Model):
    """Expense Budget Tracking"""
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    organization = models.ForeignKey(
        BaseUserModel, on_delete=models.CASCADE,
        limit_choices_to={'role': 'organization'}
    )
    category = models.ForeignKey(
        ExpenseCategory, on_delete=models.CASCADE,
        related_name='budgets'
    )
    
    # Budget Period
    year = models.IntegerField()
    month = models.IntegerField(null=True, blank=True)  # Null for yearly budget
    
    # Budget Amounts
    allocated_budget = models.DecimalField(max_digits=12, decimal_places=2)
    spent_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    pending_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    
    # Alerts
    alert_threshold_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=80.00)
    alert_sent = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('organization', 'category', 'year', 'month')
        ordering = ['-year', '-month']
    
    @property
    def remaining_budget(self):
        return self.allocated_budget - self.spent_amount - self.pending_amount
    
    @property
    def utilization_percentage(self):
        if self.allocated_budget > 0:
            return ((self.spent_amount + self.pending_amount) / self.allocated_budget) * 100
        return 0
    
    def __str__(self):
        period = f"{self.year}-{self.month:02d}" if self.month else str(self.year)
        return f"{self.category.name} - {period} - ₹{self.allocated_budget}"


class ExpenseReport(models.Model):
    """Expense Reports"""
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    organization = models.ForeignKey(
        BaseUserModel, on_delete=models.CASCADE,
        limit_choices_to={'role': 'organization'}
    )
    employee = models.ForeignKey(
        BaseUserModel, on_delete=models.CASCADE,
        limit_choices_to={'role': 'user'},
        related_name='expense_reports'
    )
    
    # Report Period
    report_name = models.CharField(max_length=255)
    start_date = models.DateField()
    end_date = models.DateField()
    
    # Expenses
    expenses = models.ManyToManyField(Expense, related_name='reports')
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    total_reimbursed = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=[
            ('draft', 'Draft'),
            ('submitted', 'Submitted'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected')
        ],
        default='draft'
    )
    
    submitted_at = models.DateTimeField(null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(
        BaseUserModel, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='approved_expense_reports'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-start_date']
    
    def __str__(self):
        return f"{self.report_name} - {self.employee.email}"
