"""
Broadcast Management Serializers
"""

from rest_framework import serializers
from .models import Broadcast, BroadcastRecipient, BroadcastTemplate
from AuthN.models import BaseUserModel


class BroadcastSerializer(serializers.ModelSerializer):
    created_by_email = serializers.EmailField(source='created_by.email', read_only=True)
    created_by_name = serializers.CharField(source='created_by.own_user_profile.user_name', read_only=True)
    target_users_detail = serializers.SerializerMethodField()
    
    def get_target_users_detail(self, obj):
        return [{'id': str(u.id), 'email': u.email, 'name': u.own_user_profile.user_name} for u in obj.target_users.all()]
    
    class Meta:
        model = Broadcast
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'published_at']


class BroadcastRecipientSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_name = serializers.CharField(source='user.own_user_profile.user_name', read_only=True)
    broadcast_title = serializers.CharField(source='broadcast.title', read_only=True)
    
    class Meta:
        model = BroadcastRecipient
        fields = '__all__'
        read_only_fields = ['id', 'created_at']


class BroadcastTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = BroadcastTemplate
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

