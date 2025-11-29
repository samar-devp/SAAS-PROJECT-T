"""
Expense Management Serializers
"""

from rest_framework import serializers
from .models import (
    ExpenseCategory, Expense, ExpensePolicy,
    ExpenseApprovalWorkflow, ExpenseReimbursement,
    ExpenseBudget, ExpenseReport
)
from AuthN.models import BaseUserModel


class ExpenseCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ExpenseCategory
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class ExpenseCategoryUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExpenseCategory
        fields = '__all__'
        read_only_fields = ['id', 'admin', 'organization', 'created_at', 'updated_at']


class ExpenseSerializer(serializers.ModelSerializer):
    employee_email = serializers.EmailField(source='employee.email', read_only=True)
    employee_name = serializers.CharField(source='employee.own_user_profile.user_name', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    approved_by_email = serializers.EmailField(source='approved_by.email', read_only=True, allow_null=True)
    project_name = serializers.CharField(source='project.name', read_only=True, allow_null=True)
    task_title = serializers.CharField(source='task.title', read_only=True, allow_null=True)
    created_by_email = serializers.EmailField(source='created_by.email', read_only=True, allow_null=True)
    
    class Meta:
        model = Expense
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class ExpensePolicySerializer(serializers.ModelSerializer):
    organization_email = serializers.EmailField(source='organization.email', read_only=True)
    created_by_email = serializers.EmailField(source='created_by.email', read_only=True, allow_null=True)
    
    class Meta:
        model = ExpensePolicy
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class ExpenseApprovalWorkflowSerializer(serializers.ModelSerializer):
    approver_email = serializers.EmailField(source='approver.email', read_only=True)
    approver_name = serializers.CharField(source='approver.own_user_profile.user_name', read_only=True)
    expense_title = serializers.CharField(source='expense.title', read_only=True)
    
    class Meta:
        model = ExpenseApprovalWorkflow
        fields = '__all__'
        read_only_fields = ['id', 'created_at']


class ExpenseReimbursementSerializer(serializers.ModelSerializer):
    employee_email = serializers.EmailField(source='employee.email', read_only=True)
    employee_name = serializers.CharField(source='employee.own_user_profile.user_name', read_only=True)
    processed_by_email = serializers.EmailField(source='processed_by.email', read_only=True, allow_null=True)
    expenses_detail = ExpenseSerializer(source='expenses', many=True, read_only=True)
    
    class Meta:
        model = ExpenseReimbursement
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class ExpenseBudgetSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    remaining_budget = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    utilization_percentage = serializers.DecimalField(max_digits=5, decimal_places=2, read_only=True)
    
    class Meta:
        model = ExpenseBudget
        fields = '__all__'
        read_only_fields = ['id', 'remaining_budget', 'utilization_percentage', 'created_at', 'updated_at']


class ExpenseReportSerializer(serializers.ModelSerializer):
    employee_email = serializers.EmailField(source='employee.email', read_only=True)
    employee_name = serializers.CharField(source='employee.own_user_profile.user_name', read_only=True)
    approved_by_email = serializers.EmailField(source='approved_by.email', read_only=True, allow_null=True)
    expenses_detail = ExpenseSerializer(source='expenses', many=True, read_only=True)
    
    class Meta:
        model = ExpenseReport
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']
