"""
Visit Management Serializers
"""

from rest_framework import serializers
from .models import VisitAssignment, VisitTemplate, VisitChecklist, VisitReport
from AuthN.models import BaseUserModel


class VisitAssignmentSerializer(serializers.ModelSerializer):
    assigned_user_email = serializers.EmailField(source='assigned_user.email', read_only=True)
    assigned_user_name = serializers.CharField(source='assigned_user.own_user_profile.user_name', read_only=True)
    created_by_email = serializers.EmailField(source='created_by.email', read_only=True, allow_null=True)
    
    class Meta:
        model = VisitAssignment
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class VisitTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = VisitTemplate
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class VisitChecklistSerializer(serializers.ModelSerializer):
    class Meta:
        model = VisitChecklist
        fields = '__all__'
        read_only_fields = ['id', 'created_at']


class VisitReportSerializer(serializers.ModelSerializer):
    visit_detail = VisitAssignmentSerializer(source='visit', read_only=True)
    created_by_email = serializers.EmailField(source='created_by.email', read_only=True, allow_null=True)
    
    class Meta:
        model = VisitReport
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

