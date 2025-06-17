from rest_framework import serializers
from .models import *

class LeaveTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveType
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

class LeaveTypeUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveType
        fields = '__all__'
        read_only_fields = ['id', 'admin', 'organization', 'created_at', 'updated_at']



class EmployeeLeaveBalanceSerializer(serializers.ModelSerializer):
    assigned = serializers.IntegerField(read_only=True)
    balance = serializers.IntegerField(read_only=True)

    class Meta:
        model = EmployeeLeaveBalance
        fields = '__all__'
        read_only_fields = ['id', 'assigned', 'balance', 'updated_at']



class EmployeeLeaveBalanceUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeLeaveBalance
        fields = '__all__'
        read_only_fields = ['id', 'assigned', 'balance', 'updated_at', 'admin', 'user', 'year']





class LeaveApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveApplication
        fields = '__all__'
        read_only_fields = ['id', 'status', 'created_at', 'updated_at']

class LeaveApplicationUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveApplication
        fields = '__all__'
        read_only_fields = ['id', 'user', 'admin', 'organization', 'created_at', 'updated_at']
