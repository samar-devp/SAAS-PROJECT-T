from rest_framework import serializers
from .models import *

class SystemOwnerSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemOwner
        fields = ['id', 'owner_name', 'email', 'username', 'password', 'is_active', 'created_at']
        extra_kwargs = {
            'password': {'write_only': True},  # Password hidden in response
            'is_active': {'read_only': True},  # Prevent modification of `is_active`
            'created_at': {'read_only': True},  # Auto-generated field
        }
        

class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ['organization_name', 'email', 'username', 'password']
        extra_kwargs = {
            'password': {'write_only': True},  # Password hidden in response
        }