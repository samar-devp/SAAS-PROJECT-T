"""
Onboarding Management Serializers
"""

from rest_framework import serializers
from .models import (
    OnboardingTemplate, OnboardingChecklist, OnboardingProcess,
    OnboardingTask, DocumentType, EmployeeDocument
)
from AuthN.models import BaseUserModel


class OnboardingTemplateSerializer(serializers.ModelSerializer):
    organization_email = serializers.EmailField(source='organization.email', read_only=True)
    admin_email = serializers.EmailField(source='admin.email', read_only=True, allow_null=True)
    
    class Meta:
        model = OnboardingTemplate
        fields = '__all__'
        read_only_fields = ['id', 'usage_count', 'created_at', 'updated_at']


class OnboardingChecklistSerializer(serializers.ModelSerializer):
    template_name = serializers.CharField(source='template.name', read_only=True)
    
    class Meta:
        model = OnboardingChecklist
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class OnboardingProcessSerializer(serializers.ModelSerializer):
    organization_email = serializers.EmailField(source='organization.email', read_only=True)
    employee_email = serializers.EmailField(source='employee.email', read_only=True, allow_null=True)
    template_name = serializers.CharField(source='template.name', read_only=True, allow_null=True)
    assigned_to_email = serializers.EmailField(source='assigned_to.email', read_only=True, allow_null=True)
    
    class Meta:
        model = OnboardingProcess
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class OnboardingTaskSerializer(serializers.ModelSerializer):
    onboarding_process_employee_name = serializers.CharField(
        source='onboarding_process.employee_name', read_only=True
    )
    checklist_item_title = serializers.CharField(
        source='checklist_item.title', read_only=True, allow_null=True
    )
    assigned_to_email = serializers.EmailField(source='assigned_to.email', read_only=True, allow_null=True)
    completed_by_email = serializers.EmailField(source='completed_by.email', read_only=True, allow_null=True)
    
    class Meta:
        model = OnboardingTask
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class DocumentTypeSerializer(serializers.ModelSerializer):
    organization_email = serializers.EmailField(source='organization.email', read_only=True)
    
    class Meta:
        model = DocumentType
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class EmployeeDocumentSerializer(serializers.ModelSerializer):
    employee_email = serializers.EmailField(source='employee.email', read_only=True)
    employee_name = serializers.CharField(source='employee.own_user_profile.user_name', read_only=True, allow_null=True)
    document_type_name = serializers.CharField(source='document_type.name', read_only=True)
    verified_by_email = serializers.EmailField(source='verified_by.email', read_only=True, allow_null=True)
    
    class Meta:
        model = EmployeeDocument
        fields = '__all__'
        read_only_fields = ['id', 'uploaded_at', 'updated_at']

