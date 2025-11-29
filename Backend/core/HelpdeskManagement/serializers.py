"""
Helpdesk Management Serializers
"""

from rest_framework import serializers
from .models import (
    TicketCategory, Ticket, TicketComment, TicketAssignmentRule,
    SLAPolicy, TicketEscalationLog
)
from AuthN.models import BaseUserModel


class TicketCategorySerializer(serializers.ModelSerializer):
    organization_email = serializers.EmailField(source='organization.email', read_only=True)
    admin_email = serializers.EmailField(source='admin.email', read_only=True, allow_null=True)
    
    class Meta:
        model = TicketCategory
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class TicketSerializer(serializers.ModelSerializer):
    organization_email = serializers.EmailField(source='organization.email', read_only=True)
    admin_email = serializers.EmailField(source='admin.email', read_only=True, allow_null=True)
    created_by_email = serializers.EmailField(source='created_by.email', read_only=True, allow_null=True)
    assigned_to_email = serializers.EmailField(source='assigned_to.email', read_only=True, allow_null=True)
    category_name = serializers.CharField(source='category.name', read_only=True, allow_null=True)
    resolved_by_email = serializers.EmailField(source='resolved_by.email', read_only=True, allow_null=True)
    closed_by_email = serializers.EmailField(source='closed_by.email', read_only=True, allow_null=True)
    
    class Meta:
        model = Ticket
        fields = '__all__'
        read_only_fields = ['id', 'ticket_number', 'created_at', 'updated_at']


class TicketCommentSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_name = serializers.CharField(source='user.own_user_profile.user_name', read_only=True, allow_null=True)
    ticket_number = serializers.CharField(source='ticket.ticket_number', read_only=True)
    
    class Meta:
        model = TicketComment
        fields = '__all__'
        read_only_fields = ['id', 'created_at']


class TicketAssignmentRuleSerializer(serializers.ModelSerializer):
    organization_email = serializers.EmailField(source='organization.email', read_only=True)
    assign_to_user_email = serializers.EmailField(source='assign_to_user.email', read_only=True, allow_null=True)
    category_name = serializers.CharField(source='category.name', read_only=True, allow_null=True)
    
    class Meta:
        model = TicketAssignmentRule
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class SLAPolicySerializer(serializers.ModelSerializer):
    organization_email = serializers.EmailField(source='organization.email', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True, allow_null=True)
    escalation_to_email = serializers.EmailField(source='escalation_to.email', read_only=True, allow_null=True)
    
    class Meta:
        model = SLAPolicy
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class TicketEscalationLogSerializer(serializers.ModelSerializer):
    ticket_number = serializers.CharField(source='ticket.ticket_number', read_only=True)
    escalated_from_email = serializers.EmailField(source='escalated_from.email', read_only=True, allow_null=True)
    escalated_to_email = serializers.EmailField(source='escalated_to.email', read_only=True, allow_null=True)
    
    class Meta:
        model = TicketEscalationLog
        fields = '__all__'
        read_only_fields = ['id', 'escalated_at']

