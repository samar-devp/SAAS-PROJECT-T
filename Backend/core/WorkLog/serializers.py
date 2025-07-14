# serializers.py
from rest_framework import serializers
from .models import Attendance
from datetime import datetime

class AttendanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attendance
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'total_working_seconds', 'overtime_minutes']

    def validate(self, data):
        if not data.get('check_in_time') and not data.get('check_out_time'):
            raise serializers.ValidationError("At least check_in_time or check_out_time is required.")
        return data
