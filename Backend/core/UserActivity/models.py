from django.db import models
from AuthN.models import *

# Create your models here.
class Location(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    admin = models.ForeignKey(AdminProfile, limit_choices_to={'role': 'admin'},on_delete=models.CASCADE)
    organization = models.ForeignKey(OrganizationProfile, limit_choices_to={'role': 'organization'},on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    address = models.TextField()
    district = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    pincode = models.CharField(max_length=10)
    country = models.CharField(max_length=100)
    latitude = models.DecimalField(max_digits=10, decimal_places=7)
    longitude = models.DecimalField(max_digits=10, decimal_places=7)
    radius_in_meters = models.IntegerField(default=100)
    is_active = models.BooleanField(default=True)
    location_type = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class UserLiveLocation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(BaseUserModel, on_delete=models.CASCADE)
    admin = models.ForeignKey(AdminProfile, on_delete=models.CASCADE)
    organization = models.ForeignKey(OrganizationProfile, on_delete=models.CASCADE)
    latitude = models.DecimalField(max_digits=10, decimal_places=7)
    longitude = models.DecimalField(max_digits=10, decimal_places=7)
    location_accuracy = models.FloatField()
    speed = models.FloatField()
    battery_percentage = models.IntegerField()
    is_charging = models.BooleanField(default=False)
    address = models.TextField()
    source = models.CharField(max_length=100)
    captured_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
