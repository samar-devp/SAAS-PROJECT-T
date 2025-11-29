"""
Notes Management Serializers
"""

from rest_framework import serializers
from .models import NoteCategory, Note, NoteComment, NoteVersion, NoteTemplate
from AuthN.models import BaseUserModel


class NoteCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = NoteCategory
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class NoteSerializer(serializers.ModelSerializer):
    created_by_email = serializers.EmailField(source='created_by.email', read_only=True)
    created_by_name = serializers.CharField(source='created_by.own_user_profile.user_name', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True, allow_null=True)
    shared_with_detail = serializers.SerializerMethodField()
    
    def get_shared_with_detail(self, obj):
        return [{'id': str(u.id), 'email': u.email, 'name': u.own_user_profile.user_name} for u in obj.shared_with.all()]
    
    class Meta:
        model = Note
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class NoteCommentSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_name = serializers.CharField(source='user.own_user_profile.user_name', read_only=True)
    
    class Meta:
        model = NoteComment
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class NoteVersionSerializer(serializers.ModelSerializer):
    changed_by_email = serializers.EmailField(source='changed_by.email', read_only=True, allow_null=True)
    
    class Meta:
        model = NoteVersion
        fields = '__all__'
        read_only_fields = ['id', 'created_at']


class NoteTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = NoteTemplate
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

