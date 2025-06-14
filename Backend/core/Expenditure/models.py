from django.db import models
from AuthN.models import *
# Create your models here.
class ExpenseCategory(models.Model):
    id = models.BigAutoField(primary_key=True)
    admin = models.ForeignKey(BaseUserModel, on_delete=models.CASCADE, related_name="admin_expense_off")
    organization = models.ForeignKey(BaseUserModel, on_delete=models.CASCADE, related_name="organization_expense_off")
    name = models.CharField(max_length=255, default="Service Expense")
    description = models.CharField(max_length=255, default="Default Service Expense")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)