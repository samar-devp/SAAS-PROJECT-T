from django.db import models
from AuthN.models import *
import uuid

# Create your models here.

class UserLocationHistory(models.Model):
    """Store historical location data for users"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        BaseUserModel, 
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'user'},
        related_name='location_history'
    )
    admin = models.ForeignKey(
        BaseUserModel,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'admin'},
        related_name='tracked_locations',
        null=True,
        blank=True
    )
    organization = models.ForeignKey(
        BaseUserModel,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'organization'},
        related_name='org_location_history',
        null=True,
        blank=True
    )
    
    # Location coordinates
    latitude = models.DecimalField(max_digits=10, decimal_places=7)
    longitude = models.DecimalField(max_digits=10, decimal_places=7)
    
    # Additional location metadata
    accuracy = models.FloatField(null=True, blank=True, help_text="Location accuracy in meters")
    altitude = models.FloatField(null=True, blank=True, help_text="Altitude in meters")
    speed = models.FloatField(null=True, blank=True, help_text="Speed in m/s")
    heading = models.FloatField(null=True, blank=True, help_text="Heading in degrees")
    
    # Device information
    battery_percentage = models.IntegerField(null=True, blank=True)
    is_charging = models.BooleanField(default=False)
    is_moving = models.BooleanField(default=False)
    
    # Address information
    address = models.TextField(null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    state = models.CharField(max_length=100, null=True, blank=True)
    country = models.CharField(max_length=100, null=True, blank=True)
    pincode = models.CharField(max_length=20, null=True, blank=True)
    
    # Source and metadata
    source = models.CharField(max_length=50, default='mobile', help_text="Source: mobile, web, api")
    device_id = models.CharField(max_length=255, null=True, blank=True)
    app_version = models.CharField(max_length=50, null=True, blank=True)
    
    # Timestamps
    captured_at = models.DateTimeField(help_text="When location was captured on device")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_location_history'
        ordering = ['-captured_at']
        indexes = [
            models.Index(fields=['user', '-captured_at']),
            models.Index(fields=['admin', '-captured_at']),
            models.Index(fields=['captured_at']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.captured_at}"


class UserLiveLocation(models.Model):
    """Store current/live location of users for real-time tracking"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        BaseUserModel,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'user'},
        related_name='live_location'
    )
    admin = models.ForeignKey(
        BaseUserModel,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'admin'},
        related_name='tracked_users',
        null=True,
        blank=True
    )
    organization = models.ForeignKey(
        BaseUserModel,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'organization'},
        related_name='org_tracked_users',
        null=True,
        blank=True
    )
    
    # Location coordinates
    latitude = models.DecimalField(max_digits=10, decimal_places=7)
    longitude = models.DecimalField(max_digits=10, decimal_places=7)
    
    # Additional location metadata
    accuracy = models.FloatField(null=True, blank=True)
    altitude = models.FloatField(null=True, blank=True)
    speed = models.FloatField(null=True, blank=True)
    heading = models.FloatField(null=True, blank=True)
    
    # Device information
    battery_percentage = models.IntegerField(null=True, blank=True)
    is_charging = models.BooleanField(default=False)
    is_moving = models.BooleanField(default=False)
    
    # Address information
    address = models.TextField(null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    state = models.CharField(max_length=100, null=True, blank=True)
    
    # Connection status
    is_online = models.BooleanField(default=False)
    last_seen = models.DateTimeField(auto_now=True)
    
    # Source and metadata
    source = models.CharField(max_length=50, default='mobile')
    device_id = models.CharField(max_length=255, null=True, blank=True)
    
    # Timestamps
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'user_live_location'
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['admin', '-updated_at']),
            models.Index(fields=['is_online']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - Live Location"
