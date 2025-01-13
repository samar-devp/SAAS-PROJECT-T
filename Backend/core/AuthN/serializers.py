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
        fields = ['owner', 'organization_name', 'email', 'username', 'password']
        extra_kwargs = {
            'password': {'write_only': True},  # Password hidden in response
        }


class AdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = Admin
        fields = ['organization', 'admin_name', 'email', 'username', 'password', 'is_active']
        extra_kwargs = {
            'password': {'write_only': True},  # Password will not be included in the response
        }

class SupervisorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supervisor
        fields = ['admin', 'supervisor_name', 'email', 'username', 'password', 'is_active']
        extra_kwargs = {
            'password': {'write_only': True},  # Password will not be included in the response
        }

class EmployeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        fields = ['admin', 'supervisor', 'employee_name', 'email', 'username', 'password', 'is_active']
        extra_kwargs = {
            'password': {'write_only': True},  # Password will not be included in the response
        }