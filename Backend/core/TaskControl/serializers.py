from rest_framework import serializers
from .models import TaskType

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
