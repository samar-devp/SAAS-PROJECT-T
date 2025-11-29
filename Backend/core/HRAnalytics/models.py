"""
HR Analytics Backend
Attendance analytics, Attrition reports, Cost center analytics, Salary distribution
"""

from django.db import models
from uuid import uuid4
from decimal import Decimal
from datetime import date, datetime
from AuthN.models import *


class CostCenter(models.Model):
    """Cost Centers"""
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    organization = models.ForeignKey(
        BaseUserModel, on_delete=models.CASCADE,
        limit_choices_to={'role': 'organization'},
        related_name='cost_centers'
    )
    
    code = models.CharField(max_length=50)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    parent_center = models.ForeignKey(
        'self', on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='sub_centers'
    )
    
    # Budget
    annual_budget = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('organization', 'code')
        ordering = ['code']
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class AttendanceAnalytics(models.Model):
    """Attendance Analytics - Aggregated Data"""
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    organization = models.ForeignKey(
        BaseUserModel, on_delete=models.CASCADE,
        limit_choices_to={'role': 'organization'},
        related_name='org_attendance_analytics'
    )
    employee = models.ForeignKey(
        BaseUserModel, on_delete=models.CASCADE,
        limit_choices_to={'role': 'user'},
        related_name='employee_attendance_analytics',
        null=True, blank=True
    )
    
    # Period
    period_type = models.CharField(
        max_length=20,
        choices=[('daily', 'Daily'), ('weekly', 'Weekly'), ('monthly', 'Monthly'), ('yearly', 'Yearly')],
        default='monthly'
    )
    period_start = models.DateField()
    period_end = models.DateField()
    
    # Metrics
    total_days = models.IntegerField(default=0)
    present_days = models.IntegerField(default=0)
    absent_days = models.IntegerField(default=0)
    leave_days = models.IntegerField(default=0)
    half_days = models.IntegerField(default=0)
    late_count = models.IntegerField(default=0)
    early_exit_count = models.IntegerField(default=0)
    
    # Hours
    total_working_hours = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    average_working_hours = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    overtime_hours = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # Attendance Rate
    attendance_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    punctuality_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('organization', 'employee', 'period_type', 'period_start')
        ordering = ['-period_start']
    
    def __str__(self):
        return f"Analytics - {self.period_start} to {self.period_end}"


class AttritionRecord(models.Model):
    """Employee Attrition Records"""
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    organization = models.ForeignKey(
        BaseUserModel, on_delete=models.CASCADE,
        limit_choices_to={'role': 'organization'},
        related_name='attrition_records'
    )
    employee = models.ForeignKey(
        BaseUserModel, on_delete=models.CASCADE,
        limit_choices_to={'role': 'user'},
        related_name='attrition_record'
    )
    
    # Attrition Details
    separation_type = models.CharField(
        max_length=50,
        choices=[
            ('resignation', 'Resignation'),
            ('termination', 'Termination'),
            ('retirement', 'Retirement'),
            ('end_of_contract', 'End of Contract'),
            ('death', 'Death'),
            ('other', 'Other')
        ],
        default='resignation'
    )
    separation_date = models.DateField()
    last_working_date = models.DateField()
    notice_period_days = models.IntegerField(default=0)
    
    # Reasons
    reason = models.TextField(blank=True, null=True)
    reason_category = models.CharField(
        max_length=50,
        choices=[
            ('better_opportunity', 'Better Opportunity'),
            ('salary', 'Salary Issues'),
            ('work_life_balance', 'Work-Life Balance'),
            ('management', 'Management Issues'),
            ('career_growth', 'Career Growth'),
            ('personal', 'Personal Reasons'),
            ('performance', 'Performance Issues'),
            ('other', 'Other')
        ],
        blank=True, null=True
    )
    
    # Employee Details at Separation
    tenure_months = models.IntegerField(default=0)
    department = models.CharField(max_length=100, blank=True, null=True)
    designation = models.CharField(max_length=100, blank=True, null=True)
    last_salary = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    
    # Exit Interview
    exit_interview_conducted = models.BooleanField(default=False)
    exit_interview_notes = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-separation_date']
    
    def __str__(self):
        return f"{self.employee.email} - {self.separation_type} - {self.separation_date}"


class AttritionAnalytics(models.Model):
    """Attrition Analytics - Aggregated"""
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    organization = models.ForeignKey(
        BaseUserModel, on_delete=models.CASCADE,
        limit_choices_to={'role': 'organization'},
        related_name='attrition_analytics'
    )
    
    # Period
    period_type = models.CharField(
        max_length=20,
        choices=[('monthly', 'Monthly'), ('quarterly', 'Quarterly'), ('yearly', 'Yearly')],
        default='monthly'
    )
    period_start = models.DateField()
    period_end = models.DateField()
    
    # Metrics
    total_employees_start = models.IntegerField(default=0)
    total_employees_end = models.IntegerField(default=0)
    new_joinings = models.IntegerField(default=0)
    separations = models.IntegerField(default=0)
    
    # Attrition Rate
    attrition_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    
    # By Department
    department_wise = models.JSONField(default=dict, blank=True)
    
    # By Reason
    reason_wise = models.JSONField(default=dict, blank=True)
    
    # Average Tenure
    average_tenure_months = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('organization', 'period_type', 'period_start')
        ordering = ['-period_start']
    
    def __str__(self):
        return f"Attrition Analytics - {self.period_start} to {self.period_end}"


class SalaryDistribution(models.Model):
    """Salary Distribution Analytics"""
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    organization = models.ForeignKey(
        BaseUserModel, on_delete=models.CASCADE,
        limit_choices_to={'role': 'organization'},
        related_name='salary_distributions'
    )
    
    # Period
    period_type = models.CharField(
        max_length=20,
        choices=[('monthly', 'Monthly'), ('quarterly', 'Quarterly'), ('yearly', 'Yearly')],
        default='monthly'
    )
    period_start = models.DateField()
    period_end = models.DateField()
    
    # Distribution Metrics
    total_payroll_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    average_salary = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    median_salary = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    min_salary = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    max_salary = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    
    # By Department
    department_wise = models.JSONField(default=dict, blank=True)
    
    # By Designation
    designation_wise = models.JSONField(default=dict, blank=True)
    
    # Salary Bands
    salary_bands = models.JSONField(
        default=dict,
        blank=True,
        help_text="{'0-50000': 10, '50000-100000': 20, ...}"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('organization', 'period_type', 'period_start')
        ordering = ['-period_start']
    
    def __str__(self):
        return f"Salary Distribution - {self.period_start} to {self.period_end}"


class CostCenterAnalytics(models.Model):
    """Cost Center Analytics"""
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    organization = models.ForeignKey(
        BaseUserModel, on_delete=models.CASCADE,
        limit_choices_to={'role': 'organization'},
        related_name='cost_center_analytics'
    )
    cost_center = models.ForeignKey(
        CostCenter, on_delete=models.CASCADE,
        related_name='analytics'
    )
    
    # Period
    period_type = models.CharField(
        max_length=20,
        choices=[('monthly', 'Monthly'), ('quarterly', 'Quarterly'), ('yearly', 'Yearly')],
        default='monthly'
    )
    period_start = models.DateField()
    period_end = models.DateField()
    
    # Costs
    total_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    payroll_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    operational_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    overhead_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    
    # Budget
    allocated_budget = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    budget_utilization = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    
    # Employee Count
    employee_count = models.IntegerField(default=0)
    average_cost_per_employee = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('cost_center', 'period_type', 'period_start')
        ordering = ['-period_start']
    
    def __str__(self):
        return f"{self.cost_center.name} - {self.period_start} to {self.period_end}"

