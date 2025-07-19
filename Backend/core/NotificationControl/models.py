from django.db import models
from AuthN.models import *
# Create your models here.

# class Notification(models.Model):
#     id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
#     user = models.ForeignKey(BaseUserModel, on_delete=models.CASCADE)
#     admin = models.ForeignKey(BaseUserModel, on_delete=models.CASCADE)
#     organization = models.ForeignKey(BaseUserModel, on_delete=models.CASCADE)
#     title = models.CharField(max_length=255)
#     message = models.TextField()
#     type = models.CharField(max_length=100)
#     action_url = models.CharField(max_length=255, null=True, blank=True)
#     is_read = models.BooleanField(default=False)
#     read_at = models.DateTimeField(null=True, blank=True)
#     sent_via = models.JSONField(null=True, blank=True)
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)