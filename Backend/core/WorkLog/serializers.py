# serializers.py
from rest_framework import serializers
from .models import Attendance
from datetime import datetime, date
from utils.Attendance.attendance_utils import *

class AttendanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attendance
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'total_working_seconds', 'overtime_minutes']

    def validate(self, data):
        if not data.get('check_in_time') and not data.get('check_out_time'):
            raise serializers.ValidationError("At least check_in_time or check_out_time is required.")
        return data


class AttendanceOutputSerializer(serializers.Serializer):
    id = serializers.IntegerField(allow_null=True)
    user_id = serializers.CharField(allow_null=True)  # Add user_id UUID
    employee_name = serializers.CharField()
    employee_id = serializers.CharField()
    employee_email = serializers.CharField()
    attendance_status = serializers.CharField()
    last_login_status = serializers.CharField(allow_null=True)
    check_in = serializers.CharField(allow_null=True)
    check_out = serializers.CharField(allow_null=True)
    break_duration = serializers.CharField()
    late_minutes_display = serializers.CharField()
    production_hours = serializers.CharField()
    attendance_date = serializers.CharField()
    shift_name = serializers.CharField()
    is_late = serializers.BooleanField()
    late_minutes = serializers.IntegerField()
    is_early_exit = serializers.BooleanField()
    early_exit_minutes = serializers.IntegerField()
    multiple_entries = serializers.ListField()
    remarks = serializers.CharField(allow_null=True)
    


class EditAttendanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attendance
        fields = ["check_in_time", "check_out_time", "remarks"]

    def validate(self, data):
        check_in = data.get("check_in_time")
        check_out = data.get("check_out_time")

        if check_in and check_out and check_out < check_in:
            raise serializers.ValidationError("Check-out cannot be before check-in.")

        return data
