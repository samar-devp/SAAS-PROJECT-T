"""
Organization Management Serializers
"""

from rest_framework import serializers
from .models import (
    SubscriptionPlan, OrganizationSubscription, OrganizationModule,
    OrganizationUsage, OrganizationDeactivationLog, SuperAdminAction
)
from AuthN.models import BaseUserModel


class SubscriptionPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionPlan
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class OrganizationSubscriptionSerializer(serializers.ModelSerializer):
    organization_email = serializers.EmailField(source='organization.email', read_only=True)
    plan_name = serializers.CharField(source='plan.name', read_only=True)
    plan_code = serializers.CharField(source='plan.code', read_only=True)
    
    class Meta:
        model = OrganizationSubscription
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class OrganizationModuleSerializer(serializers.ModelSerializer):
    organization_email = serializers.EmailField(source='organization.email', read_only=True)
    
    class Meta:
        model = OrganizationModule
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class OrganizationUsageSerializer(serializers.ModelSerializer):
    organization_email = serializers.EmailField(source='organization.email', read_only=True)
    
    class Meta:
        model = OrganizationUsage
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class OrganizationDeactivationLogSerializer(serializers.ModelSerializer):
    organization_email = serializers.EmailField(source='organization.email', read_only=True)
    deactivated_by_email = serializers.EmailField(source='deactivated_by.email', read_only=True, allow_null=True)
    reactivated_by_email = serializers.EmailField(source='reactivated_by.email', read_only=True, allow_null=True)
    
    class Meta:
        model = OrganizationDeactivationLog
        fields = '__all__'
        read_only_fields = ['id', 'deactivated_at']


class SuperAdminActionSerializer(serializers.ModelSerializer):
    super_admin_email = serializers.EmailField(source='super_admin.email', read_only=True, allow_null=True)
    organization_email = serializers.EmailField(source='organization.email', read_only=True, allow_null=True)
    
    class Meta:
        model = SuperAdminAction
        fields = '__all__'
        read_only_fields = ['id', 'created_at']

