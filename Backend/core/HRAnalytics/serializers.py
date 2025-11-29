"""
HR Analytics Serializers
"""

from rest_framework import serializers
from .models import (
    CostCenter, AttendanceAnalytics, AttritionRecord,
    AttritionAnalytics, SalaryDistribution, CostCenterAnalytics
)
from AuthN.models import BaseUserModel


class CostCenterSerializer(serializers.ModelSerializer):
    organization_email = serializers.EmailField(source='organization.email', read_only=True)
    parent_center_name = serializers.CharField(source='parent_center.name', read_only=True, allow_null=True)
    
    class Meta:
        model = CostCenter
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class AttendanceAnalyticsSerializer(serializers.ModelSerializer):
    organization_email = serializers.EmailField(source='organization.email', read_only=True)
    employee_email = serializers.EmailField(source='employee.email', read_only=True, allow_null=True)
    employee_name = serializers.CharField(source='employee.own_user_profile.user_name', read_only=True, allow_null=True)
    
    class Meta:
        model = AttendanceAnalytics
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class AttritionRecordSerializer(serializers.ModelSerializer):
    organization_email = serializers.EmailField(source='organization.email', read_only=True)
    employee_email = serializers.EmailField(source='employee.email', read_only=True)
    employee_name = serializers.CharField(source='employee.own_user_profile.user_name', read_only=True, allow_null=True)
    
    class Meta:
        model = AttritionRecord
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class AttritionAnalyticsSerializer(serializers.ModelSerializer):
    organization_email = serializers.EmailField(source='organization.email', read_only=True)
    
    class Meta:
        model = AttritionAnalytics
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class SalaryDistributionSerializer(serializers.ModelSerializer):
    organization_email = serializers.EmailField(source='organization.email', read_only=True)
    
    class Meta:
        model = SalaryDistribution
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class CostCenterAnalyticsSerializer(serializers.ModelSerializer):
    organization_email = serializers.EmailField(source='organization.email', read_only=True)
    cost_center_name = serializers.CharField(source='cost_center.name', read_only=True)
    cost_center_code = serializers.CharField(source='cost_center.code', read_only=True)
    
    class Meta:
        model = CostCenterAnalytics
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

