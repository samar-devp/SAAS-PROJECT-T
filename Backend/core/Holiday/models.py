from django.db import models
from AuthN.models import *

# Create your models here.
class Holiday(models.Model):
    id = models.BigAutoField(primary_key=True)  # Auto-incrementing BigInt ID
    admin = models.ForeignKey(BaseUserModel, on_delete=models.CASCADE , limit_choices_to={'role': 'admin'}, related_name="admin_holiday")
    organization = models.ForeignKey(BaseUserModel, on_delete=models.CASCADE, limit_choices_to={'role': 'organization'},related_name="organization_holiday")
    name = models.CharField(max_length=255)
    holiday_date = models.DateField()
    is_optional = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    def __str__(self):
        return self.name

