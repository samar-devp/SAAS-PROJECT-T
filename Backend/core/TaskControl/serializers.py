"""
Task Management Serializers
"""

from rest_framework import serializers
from .models import TaskType, Project, Task, TaskComment, TaskTimeLog, TaskAttachment
from AuthN.models import BaseUserModel


class TaskTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskType
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class TaskTypeUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskType
        fields = '__all__'
        read_only_fields = ['id', 'admin', 'organization', 'created_at', 'updated_at']


class ProjectSerializer(serializers.ModelSerializer):
    project_manager_email = serializers.EmailField(source='project_manager.email', read_only=True, allow_null=True)
    team_members_detail = serializers.SerializerMethodField()
    
    def get_team_members_detail(self, obj):
        return [{'id': str(m.id), 'email': m.email, 'name': m.own_user_profile.user_name} for m in obj.team_members.all()]
    
    class Meta:
        model = Project
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class TaskSerializer(serializers.ModelSerializer):
    assigned_to_email = serializers.EmailField(source='assigned_to.email', read_only=True, allow_null=True)
    assigned_to_name = serializers.CharField(source='assigned_to.own_user_profile.user_name', read_only=True, allow_null=True)
    assigned_by_email = serializers.EmailField(source='assigned_by.email', read_only=True, allow_null=True)
    project_name = serializers.CharField(source='project.name', read_only=True, allow_null=True)
    task_type_name = serializers.CharField(source='task_type.name', read_only=True)
    
    class Meta:
        model = Task
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class TaskCommentSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_name = serializers.CharField(source='user.own_user_profile.user_name', read_only=True)
    
    class Meta:
        model = TaskComment
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class TaskTimeLogSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)
    task_title = serializers.CharField(source='task.title', read_only=True)
    
    class Meta:
        model = TaskTimeLog
        fields = '__all__'
        read_only_fields = ['id', 'created_at']


class TaskAttachmentSerializer(serializers.ModelSerializer):
    uploaded_by_email = serializers.EmailField(source='uploaded_by.email', read_only=True)
    task_title = serializers.CharField(source='task.title', read_only=True)
    
    class Meta:
        model = TaskAttachment
        fields = '__all__'
        read_only_fields = ['id', 'created_at']
