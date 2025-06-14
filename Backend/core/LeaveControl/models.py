from django.db import models
import uuid
from AuthN.models import *

class LeavePolicy(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    admin = models.ForeignKey(AdminProfile, on_delete=models.CASCADE, related_name='leave_policies')
    organization = models.ForeignKey(OrganizationProfile, on_delete=models.CASCADE, related_name='leave_policies')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    leave_type = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
