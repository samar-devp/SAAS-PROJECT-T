from django.db import models
import uuid
from AuthN.models import BaseUserModel  # Adjust if your base user import is different

class Location(models.Model):
    id = models.BigAutoField(primary_key=True)
    admin = models.ForeignKey(BaseUserModel, on_delete=models.CASCADE,limit_choices_to={'role': 'admin'},related_name='locations_created')
    organization = models.ForeignKey(BaseUserModel,on_delete=models.CASCADE,limit_choices_to={'role': 'organization'},related_name='organization_locations')
    name = models.CharField(max_length=255)
    address = models.TextField()
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    radius = models.IntegerField(help_text="Radius in meters for geofencing", default=100)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

