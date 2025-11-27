# serializers.py
from rest_framework import serializers
from .models import Attendance
from datetime import datetime, date
from utils.attendance_utils import *

class AttendanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attendance
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'total_working_seconds', 'overtime_minutes']

    def validate(self, data):
        if not data.get('check_in_time') and not data.get('check_out_time'):
            raise serializers.ValidationError("At least check_in_time or check_out_time is required.")
        return data


class EmployeeAttendanceListSerializer(serializers.Serializer):
    """Serializer for employee attendance list with aggregated data"""
    id = serializers.IntegerField()
    employee_name = serializers.SerializerMethodField()
    employee_id = serializers.SerializerMethodField()
    employee_email = serializers.SerializerMethodField()
    attendance_status = serializers.CharField()
    last_login_status = serializers.SerializerMethodField()
    check_in = serializers.SerializerMethodField()
    check_out = serializers.SerializerMethodField()
    break_duration = serializers.SerializerMethodField()
    late_minutes_display = serializers.SerializerMethodField()
    production_hours = serializers.SerializerMethodField()
    attendance_date = serializers.SerializerMethodField()
    is_late = serializers.BooleanField()
    late_minutes = serializers.IntegerField()
    is_early_exit = serializers.SerializerMethodField()
    early_exit_minutes = serializers.SerializerMethodField()
        # 👇👇 NEW FIELD (MULTIPLE CHECKINS LIST)
    multiple_entries = serializers.ListField(
        child=serializers.DictField(),
        required=False
    )
    remarks = serializers.CharField()
    
    def get_employee_name(self, obj):
        if isinstance(obj, dict):
            user = obj.get('user')
            if user and hasattr(user, 'own_user_profile'):
                return user.own_user_profile.user_name
        elif hasattr(obj, 'user') and hasattr(obj.user, 'own_user_profile'):
            return obj.user.own_user_profile.user_name
        return "N/A"
    
    def get_employee_id(self, obj):
        if isinstance(obj, dict):
            user = obj.get('user')
            if user and hasattr(user, 'own_user_profile'):
                return user.own_user_profile.user_id or "N/A"
        elif hasattr(obj, 'user') and hasattr(obj.user, 'own_user_profile'):
            return obj.user.own_user_profile.user_id or "N/A"
        return "N/A"
    
    def get_employee_email(self, obj):
        if isinstance(obj, dict):
            user = obj.get('user')
            if user:
                return user.email
        elif hasattr(obj, 'user'):
            return obj.user.email
        return "N/A"
    
    def get_check_in(self, obj):
        if isinstance(obj, dict):
            check_in_time = obj.get('first_check_in')
        else:
            check_in_time = obj.check_in_time if hasattr(obj, 'check_in_time') else None
        
        if check_in_time:
            if isinstance(check_in_time, datetime):
                return format_datetime(check_in_time)
            return str(check_in_time)
        return None
    
    def get_check_out(self, obj):
        if isinstance(obj, dict):
            check_out_time = obj.get('last_check_out')
        else:
            check_out_time = obj.check_out_time if hasattr(obj, 'check_out_time') else None
        
        if check_out_time:
            return format_datetime(check_out_time)
        return None
    
    def get_break_duration(self, obj):
        if isinstance(obj, dict):
            break_minutes = obj.get('total_break_minutes', 0)
        else:
            break_minutes = obj.break_duration_minutes if hasattr(obj, 'break_duration_minutes') else 0
        
        if break_minutes:
            return format_minutes(break_minutes)
        return format_minutes(0)
    
    def get_late_minutes_display(self, obj):
        if isinstance(obj, dict):
            late_minutes = obj.get('late_minutes', 0)
        else:
            late_minutes = obj.late_minutes if hasattr(obj, 'late_minutes') else 0
        
        if late_minutes and late_minutes > 0:
            return format_minutes(late_minutes)
        return format_minutes(0)
    
    def get_production_hours(self, obj):
        if isinstance(obj, dict):
            total_minutes = obj.get('total_working_minutes', 0)
        else:
            total_minutes = obj.total_working_minutes if hasattr(obj, 'total_working_minutes') else 0
        
        if total_minutes:
            return format_minutes(total_minutes)
        return format_minutes(0)
    
    def get_last_login_status(self, obj):
        if isinstance(obj, dict):
            # Return: "checkin", "checkout", or None/blank
            return obj.get('last_login_status', None)
        return None
    
    def get_attendance_date(self, obj):
        if isinstance(obj, dict):
            att_date = obj.get('attendance_date')
        else:
            att_date = obj.attendance_date if hasattr(obj, 'attendance_date') else None
        
        if att_date:
            if isinstance(att_date, date):
                return format_date(att_date)
            return str(att_date)
        return None
    
    def get_is_early_exit(self, obj):
        if isinstance(obj, dict):
            # Calculate early exit based on last check-out and shift
            last_check_out = obj.get('last_check_out_time')
            assign_shift = obj.get('assign_shift')
            if last_check_out and assign_shift and assign_shift.end_time:
                from datetime import datetime
                shift_end = datetime.combine(last_check_out.date(), assign_shift.end_time)
                return last_check_out < shift_end
        elif hasattr(obj, 'is_early_exit'):
            return obj.is_early_exit
        return False
    
    def get_early_exit_minutes(self, obj):
        if isinstance(obj, dict):
            last_check_out = obj.get('last_check_out_time')
            assign_shift = obj.get('assign_shift')
            if last_check_out and assign_shift and assign_shift.end_time:
                return calculate_early_exit_minutes(last_check_out, assign_shift.end_time)
        elif hasattr(obj, 'early_exit_minutes'):
            return obj.early_exit_minutes
        return 0


class EditAttendanceSerializer(serializers.ModelSerializer):
    """Serializer for editing attendance check_in and check_out only"""
    class Meta:
        model = Attendance
        fields = ['check_in_time', 'check_out_time', 'remarks']
    
    def validate(self, data):
        check_in = data.get('check_in_time')
        check_out = data.get('check_out_time')
        
        if check_in and check_out and check_out < check_in:
            raise serializers.ValidationError("Check out time cannot be before check in time.")
        
        return data