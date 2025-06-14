import uuid
from django.db import models
from AuthN.models import *

class Attendance(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    admin = models.ForeignKey(AdminProfile, on_delete=models.CASCADE)
    organization = models.ForeignKey(OrganizationProfile, on_delete=models.CASCADE)
    attendance_date = models.DateField()
    check_in_time = models.DateTimeField(null=True, blank=True)
    check_out_time = models.DateTimeField(null=True, blank=True)
    total_working_hours = models.DurationField(null=True, blank=True)
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
    is_early_exit = models.BooleanField(default=False)
    remarks = models.TextField(null=True, blank=True)
    attachments = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)