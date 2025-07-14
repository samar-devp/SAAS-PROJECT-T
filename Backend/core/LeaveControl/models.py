from django.db import models
import uuid
from AuthN.models import *

class LeaveType(models.Model):
    id = models.BigAutoField(primary_key=True)  # Auto-incrementing BigInt ID
    admin = models.ForeignKey(BaseUserModel, on_delete=models.CASCADE, limit_choices_to={'role': 'admin'},related_name='admin_leave_policies')
    organization = models.ForeignKey(BaseUserModel, on_delete=models.CASCADE, limit_choices_to={'role': 'organization'},related_name='organization_leave_policies')
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20)
    default_count = models.PositiveIntegerField(default=0)
    is_paid = models.BooleanField(default=True)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('admin', 'code', 'is_active')

    def __str__(self):
        return f"{self.name} ({self.code})"


class EmployeeLeaveBalance(models.Model):
    id = models.BigAutoField(primary_key=True)  # Auto-incrementing BigInt ID
    admin = models.ForeignKey(BaseUserModel, on_delete=models.CASCADE, limit_choices_to={'role': 'admin'},related_name='admin_leave_balances')
    user = models.ForeignKey(BaseUserModel, on_delete=models.CASCADE, limit_choices_to={'role': 'user'},related_name='user_leave_balances')
    leave_type = models.ForeignKey(LeaveType, on_delete=models.CASCADE, related_name='employee_balances')
    year = models.PositiveIntegerField()
    used = models.PositiveIntegerField(default=0)
    pending = models.PositiveIntegerField(default=0)
    carried_forward = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'leave_type', 'year', 'is_active')

    @property
    def assigned(self):
        return self.leave_type.default_count + self.carried_forward

    @property
    def balance(self):
        return self.assigned - self.used

    def __str__(self):
        return f"{self.user.username} - {self.leave_type.code} ({self.balance} days)"

class LeaveApplication(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    )
    id = models.BigAutoField(primary_key=True)  # Auto-incrementing BigInt ID
    admin = models.ForeignKey(BaseUserModel, on_delete=models.CASCADE, limit_choices_to={'role': 'admin'},related_name='admin_leave_applications')
    user = models.ForeignKey(BaseUserModel, on_delete=models.CASCADE, limit_choices_to={'role': 'user'},related_name='user_leave_applications')
    leave_type = models.ForeignKey(LeaveType, on_delete=models.CASCADE)
    from_date = models.DateField()
    to_date = models.DateField()
    total_days = models.DecimalField(max_digits=5, decimal_places=2)
    reason = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    applied_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(blank=True, null=True)
    reviewed_by = models.ForeignKey(BaseUserModel, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_leaves')
    comments = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-applied_at']

    def __str__(self):
        return f"{self.employee.username} - {self.leave_type.code} ({self.from_date} to {self.to_date})"
