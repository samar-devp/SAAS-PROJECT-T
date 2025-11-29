"""
Additional Utility APIs for Attendance/WorkLog
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.db.models import Q, Count, Sum, Avg
from django.utils import timezone
from datetime import datetime, date, timedelta

from .models import Attendance
from AuthN.models import BaseUserModel, UserProfile
from utils.pagination_utils import CustomPagination


class AttendanceDashboardAPIView(APIView):
    """Attendance Dashboard Statistics"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, org_id):
        try:
            organization = get_object_or_404(BaseUserModel, id=org_id, role='organization')
            
            today = date.today()
            
            # Today's Statistics
            today_attendance = Attendance.objects.filter(
                user__own_user_profile__organization=organization,
                attendance_date=today
            )
            
            present = today_attendance.filter(check_in_time__isnull=False).count()
            absent = UserProfile.objects.filter(
                organization=organization,
                user__is_active=True
            ).count() - present
            
            # This Month Statistics
            month_start = date(today.year, today.month, 1)
            month_attendance = Attendance.objects.filter(
                user__own_user_profile__organization=organization,
                attendance_date__gte=month_start,
                attendance_date__lte=today
            )
            
            total_working_hours = month_attendance.aggregate(
                total=Sum('total_working_minutes')
            )['total'] or 0
            total_working_hours = total_working_hours / 60  # Convert to hours
            
            avg_working_hours = month_attendance.aggregate(
                avg=Avg('total_working_minutes')
            )['avg'] or 0
            avg_working_hours = avg_working_hours / 60
            
            return Response({
                "status": status.HTTP_200_OK,
                "message": "Attendance dashboard data fetched successfully",
                "data": {
                    "today": {
                        "present": present,
                        "absent": absent,
                        "attendance_rate": round((present / (present + absent) * 100) if (present + absent) > 0 else 0, 2)
                    },
                    "this_month": {
                        "total_working_hours": round(total_working_hours, 2),
                        "average_working_hours": round(avg_working_hours, 2),
                        "total_records": month_attendance.count()
                    }
                }
            })
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": {}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class EmployeeAttendanceHistoryAPIView(APIView):
    """Get employee attendance history"""
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination
    
    def get(self, request, org_id, employee_id):
        try:
            organization = get_object_or_404(BaseUserModel, id=org_id, role='organization')
            employee = get_object_or_404(BaseUserModel, id=employee_id, role='user')
            
            attendances = Attendance.objects.filter(
                user=employee
            ).order_by('-attendance_date')
            
            # Filters
            from_date = request.query_params.get('from_date')
            to_date = request.query_params.get('to_date')
            status_filter = request.query_params.get('status')  # present, absent
            
            if from_date:
                attendances = attendances.filter(attendance_date__gte=from_date)
            if to_date:
                attendances = attendances.filter(attendance_date__lte=to_date)
            if status_filter == 'present':
                attendances = attendances.filter(check_in_time__isnull=False)
            elif status_filter == 'absent':
                attendances = attendances.filter(check_in_time__isnull=True)
            
            paginator = self.pagination_class()
            paginated_qs = paginator.paginate_queryset(attendances, request)
            
            # Serialize manually
            data = []
            for att in paginated_qs:
                data.append({
                    "id": str(att.id),
                    "attendance_date": att.attendance_date.isoformat(),
                    "check_in_time": att.check_in_time.isoformat() if att.check_in_time else None,
                    "check_out_time": att.check_out_time.isoformat() if att.check_out_time else None,
                    "total_working_minutes": att.total_working_minutes,
                    "status": "present" if att.check_in_time else "absent"
                })
            
            pagination_data = paginator.get_paginated_response(data)
            
            # Summary
            total_days = attendances.count()
            present_days = attendances.filter(check_in_time__isnull=False).count()
            total_hours = sum([a.total_working_minutes or 0 for a in attendances]) / 60
            
            pagination_data["summary"] = {
                "total_days": total_days,
                "present_days": present_days,
                "absent_days": total_days - present_days,
                "total_hours": round(total_hours, 2),
                "attendance_rate": round((present_days / total_days * 100) if total_days > 0 else 0, 2)
            }
            
            return Response({
                "status": status.HTTP_200_OK,
                "message": "Attendance history fetched successfully",
                "data": pagination_data
            })
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

