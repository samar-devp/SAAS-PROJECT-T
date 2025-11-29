from rest_framework import serializers
from .models import UserLocationHistory, UserLiveLocation
from AuthN.models import BaseUserModel


class UserLocationHistorySerializer(serializers.ModelSerializer):
    """Serializer for location history"""
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_name = serializers.CharField(source='user.own_user_profile.user_name', read_only=True)
    admin_email = serializers.EmailField(source='admin.email', read_only=True, allow_null=True)
    
    class Meta:
        model = UserLocationHistory
        fields = [
            'id', 'user', 'user_email', 'user_name', 'admin', 'admin_email',
            'organization', 'latitude', 'longitude', 'accuracy', 'altitude',
            'speed', 'heading', 'battery_percentage', 'is_charging', 'is_moving',
            'address', 'city', 'state', 'country', 'pincode', 'source',
            'device_id', 'app_version', 'captured_at', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class UserLiveLocationSerializer(serializers.ModelSerializer):
    """Serializer for live location"""
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_name = serializers.CharField(source='user.own_user_profile.user_name', read_only=True)
    admin_email = serializers.EmailField(source='admin.email', read_only=True, allow_null=True)
    
    class Meta:
        model = UserLiveLocation
        fields = [
            'id', 'user', 'user_email', 'user_name', 'admin', 'admin_email',
            'organization', 'latitude', 'longitude', 'accuracy', 'altitude',
            'speed', 'heading', 'battery_percentage', 'is_charging', 'is_moving',
            'address', 'city', 'state', 'is_online', 'last_seen', 'source',
            'device_id', 'updated_at', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'last_seen']


class LocationUpdateSerializer(serializers.Serializer):
    """Serializer for location update from mobile device"""
    latitude = serializers.DecimalField(max_digits=10, decimal_places=7, required=True)
    longitude = serializers.DecimalField(max_digits=10, decimal_places=7, required=True)
    accuracy = serializers.FloatField(required=False, allow_null=True)
    altitude = serializers.FloatField(required=False, allow_null=True)
    speed = serializers.FloatField(required=False, allow_null=True)
    heading = serializers.FloatField(required=False, allow_null=True)
    battery_percentage = serializers.IntegerField(required=False, allow_null=True)
    is_charging = serializers.BooleanField(required=False, default=False)
    is_moving = serializers.BooleanField(required=False, default=False)
    address = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    city = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    state = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    country = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    pincode = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    source = serializers.CharField(required=False, default='mobile')
    device_id = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    app_version = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    captured_at = serializers.DateTimeField(required=False, allow_null=True)

