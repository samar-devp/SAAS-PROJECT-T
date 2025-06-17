import uuid
from django.db import models
from AuthN.models import *

from .models import ServiceShift  # shift model ka import

class Attendance(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(BaseUserModel, on_delete=models.CASCADE, limit_choices_to={'role': 'user'}, related_name="user_self_attendnace")
    admin = models.ForeignKey(BaseUserModel, on_delete=models.CASCADE, limit_choices_to={'role': 'admin'}, related_name="admin_attendnace")
    organization = models.ForeignKey(BaseUserModel, on_delete=models.CASCADE, limit_choices_to={'role': 'organization'}, related_name="organization_attendances")
    
    assign_shift = models.ForeignKey(  # ✅ New field
        ServiceShift,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="shift_attendance"
    )

    attendance_date = models.DateField()
    check_in_time = models.DateTimeField(null=True, blank=True)
    check_out_time = models.DateTimeField(null=True, blank=True)
    total_working_minutes = models.IntegerField(null=True, blank=True)  # ✅ Use this instead of DurationField
    break_duration_minutes = models.IntegerField(default=0)
    attendance_status = models.CharField(max_length=50)
    check_in_location = models.TextField(null=True, blank=True)
    check_out_location = models.TextField(null=True, blank=True)
    check_in_latitude = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)
    check_in_longitude = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)
    check_out_latitude = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)
    check_out_longitude = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)
    marked_by = models.CharField(max_length=100)
    is_late = models.BooleanField(default=False)
    late_minutes = models.IntegerField(default=0)
    is_early_exit = models.BooleanField(default=False)
    early_exit_minutes = models.IntegerField(default=0)
    remarks = models.TextField(null=True, blank=True)
    attachments = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)