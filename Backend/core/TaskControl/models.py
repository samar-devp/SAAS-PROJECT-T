from django.db import models
from AuthN.models import *
# Create your models here.

class TaskType(models.Model):
    id = models.BigAutoField(primary_key=True)
    admin = models.ForeignKey(BaseUserModel, on_delete=models.CASCADE, limit_choices_to={'role': 'admin'},related_name="admin_task_type")
    organization = models.ForeignKey(BaseUserModel, on_delete=models.CASCADE, limit_choices_to={'role': 'organization'},related_name="organization_task_type")
    name = models.CharField(max_length=255, null=True, blank=True, default="Service Task")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)                



# class UserTask(models.Model):
#     id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
#     admin = models.ForeignKey(AdminProfile, on_delete=models.CASCADE)
#     organization = models.ForeignKey(OrganizationProfile, on_delete=models.CASCADE)
#     assigned_to_user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
#     task_type = models.ForeignKey(TaskType, on_delete=models.CASCADE)
#     title = models.CharField(max_length=255)
#     description = models.TextField(blank=True, null=True)
#     priority = models.CharField(max_length=50)
#     status = models.CharField(max_length=50)
#     start_time = models.DateTimeField()
#     end_time = models.DateTimeField()
#     is_recurring = models.BooleanField(default=False)
#     recurrence_frequency = models.CharField(max_length=50, blank=True, null=True)
#     recurrence_end_date = models.DateField(blank=True, null=True)
#     week_day = models.CharField(max_length=20, blank=True, null=True)
#     month_date = models.IntegerField(blank=True, null=True)
#     comment = models.TextField(blank=True, null=True)
#     attachments = models.JSONField(blank=True, null=True)
#     tags = models.JSONField(blank=True, null=True)
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)
