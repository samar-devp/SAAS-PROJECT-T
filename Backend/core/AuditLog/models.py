from django.db import models
from AuthN.models import *
# Create your models here.

# class AuditLog(models.Model):
#     id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
#     organization = models.ForeignKey(BaseUserModel, on_delete=models.CASCADE)
#     performed_by_admin = models.ForeignKey(BaseUserModel, null=True, blank=True, on_delete=models.SET_NULL)
#     performed_by_user = models.ForeignKey(BaseUserModel, null=True, blank=True, on_delete=models.SET_NULL)
#     performed_by_system_user = models.ForeignKey(BaseUserModel, null=True, blank=True, on_delete=models.SET_NULL)
#     action_type = models.CharField(max_length=100)
#     module_name = models.CharField(max_length=100)
#     action_on_table = models.CharField(max_length=100)
#     action_on_record_id = models.UUIDField()
#     summary_text = models.TextField()
#     change_details = models.JSONField()
#     source_ip = models.CharField(max_length=100)
#     user_agent = models.TextField()
#     status = models.CharField(max_length=50, default='Success')
#     created_at = models.DateTimeField(auto_now_add=True)
