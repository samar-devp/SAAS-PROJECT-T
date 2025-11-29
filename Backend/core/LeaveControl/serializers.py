"""
Comprehensive Leave Management Serializers
"""

from rest_framework import serializers
from .models import (
    LeaveType, LeavePolicy, EmployeeLeaveBalance, LeaveApplication,
    CompensatoryOff, LeaveEncashment, LeaveBalanceAdjustment,
    LeaveAccrualLog, LeaveApprovalDelegation, LeaveCalendarEvent
)
from AuthN.models import BaseUserModel


class LeaveTypeSerializer(serializers.ModelSerializer):
    admin_email = serializers.EmailField(source='admin.email', read_only=True)
    organization_email = serializers.EmailField(source='organization.email', read_only=True)
    
    class Meta:
        model = LeaveType
        fields = [
            'id', 'admin', 'organization', 'name', 'code', 'default_count', 
            'is_paid', 'is_active', 'description', 'created_at', 'updated_at',
            'admin_email', 'organization_email'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class LeaveTypeUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveType
        fields = '__all__'
        read_only_fields = ['id', 'admin', 'organization', 'created_at', 'updated_at']


class LeavePolicySerializer(serializers.ModelSerializer):
    organization_email = serializers.EmailField(source='organization.email', read_only=True)
    admin_email = serializers.EmailField(source='admin.email', read_only=True, allow_null=True)
    created_by_email = serializers.EmailField(source='created_by.email', read_only=True, allow_null=True)
    
    class Meta:
        model = LeavePolicy
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class EmployeeLeaveBalanceSerializer(serializers.ModelSerializer):
    assigned = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)
    balance = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)
    total_available = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)
    closing_balance = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_name = serializers.CharField(source='user.own_user_profile.user_name', read_only=True)
    leave_type_name = serializers.CharField(source='leave_type.name', read_only=True)
    leave_type_code = serializers.CharField(source='leave_type.code', read_only=True)
    
    class Meta:
        model = EmployeeLeaveBalance
        fields = '__all__'
        read_only_fields = ['id', 'assigned', 'balance', 'total_available', 'closing_balance', 'updated_at']


class EmployeeLeaveBalanceUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeLeaveBalance
        fields = '__all__'
        read_only_fields = ['id', 'assigned', 'balance', 'total_available', 'closing_balance', 'updated_at', 'admin', 'user', 'year']


class LeaveApplicationSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_name = serializers.CharField(source='user.own_user_profile.user_name', read_only=True)
    leave_type_name = serializers.CharField(source='leave_type.name', read_only=True)
    leave_type_code = serializers.CharField(source='leave_type.code', read_only=True)
    reviewed_by_email = serializers.EmailField(source='reviewed_by.email', read_only=True, allow_null=True)
    current_approver_email = serializers.EmailField(source='current_approver.email', read_only=True, allow_null=True)
    
    class Meta:
        model = LeaveApplication
        fields = '__all__'
        read_only_fields = ['id', 'applied_at', 'updated_at']


class LeaveApplicationUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveApplication
        fields = '__all__'
        read_only_fields = ['id', 'user', 'admin', 'organization', 'applied_at', 'updated_at']


class CompensatoryOffSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_name = serializers.CharField(source='user.own_user_profile.user_name', read_only=True)
    approved_by_email = serializers.EmailField(source='approved_by.email', read_only=True, allow_null=True)
    
    class Meta:
        model = CompensatoryOff
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class LeaveEncashmentSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_name = serializers.CharField(source='user.own_user_profile.user_name', read_only=True)
    leave_type_name = serializers.CharField(source='leave_type.name', read_only=True)
    approved_by_email = serializers.EmailField(source='approved_by.email', read_only=True, allow_null=True)
    
    class Meta:
        model = LeaveEncashment
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class LeaveBalanceAdjustmentSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_name = serializers.CharField(source='user.own_user_profile.user_name', read_only=True)
    leave_type_name = serializers.CharField(source='leave_type.name', read_only=True)
    approved_by_email = serializers.EmailField(source='approved_by.email', read_only=True, allow_null=True)
    created_by_email = serializers.EmailField(source='created_by.email', read_only=True, allow_null=True)
    
    class Meta:
        model = LeaveBalanceAdjustment
        fields = '__all__'
        read_only_fields = ['id', 'created_at']


class LeaveAccrualLogSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)
    leave_type_name = serializers.CharField(source='leave_type.name', read_only=True)
    
    class Meta:
        model = LeaveAccrualLog
        fields = '__all__'
        read_only_fields = ['id', 'created_at']


class LeaveApprovalDelegationSerializer(serializers.ModelSerializer):
    delegator_email = serializers.EmailField(source='delegator.email', read_only=True)
    delegate_email = serializers.EmailField(source='delegate.email', read_only=True)
    leave_types_detail = LeaveTypeSerializer(source='leave_types', many=True, read_only=True)
    
    class Meta:
        model = LeaveApprovalDelegation
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class LeaveCalendarEventSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_name = serializers.CharField(source='user.own_user_profile.user_name', read_only=True)
    leave_application_detail = LeaveApplicationSerializer(source='leave_application', read_only=True)
    
    class Meta:
        model = LeaveCalendarEvent
        fields = '__all__'
        read_only_fields = ['id', 'created_at']
