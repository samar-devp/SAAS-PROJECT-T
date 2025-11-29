"""
Dashboard and Statistics APIs for AuthN Module
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Q, Count, Sum, Avg
from django.utils import timezone
from datetime import datetime, date, timedelta

from .models import BaseUserModel, UserProfile, AdminProfile, OrganizationProfile
from WorkLog.models import Attendance
from LeaveControl.models import LeaveApplication
from PayrollSystem.models import PayrollRecord


class OrganizationDashboardAPIView(APIView):
    """Organization Dashboard Statistics"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, org_id):
        try:
            organization = get_object_or_404(BaseUserModel, id=org_id, role='organization')
            
            # Employee Statistics
            total_employees = UserProfile.objects.filter(organization=organization).count()
            active_employees = UserProfile.objects.filter(
                organization=organization,
                user__is_active=True
            ).count()
            inactive_employees = total_employees - active_employees
            
            # Admin Statistics
            total_admins = AdminProfile.objects.filter(organization=organization).count()
            active_admins = AdminProfile.objects.filter(
                organization=organization,
                user__is_active=True
            ).count()
            
            # Today's Attendance
            today = date.today()
            today_attendance = Attendance.objects.filter(
                user__own_user_profile__organization=organization,
                attendance_date=today
            ).count()
            today_present = Attendance.objects.filter(
                user__own_user_profile__organization=organization,
                attendance_date=today,
                check_in_time__isnull=False
            ).count()
            today_absent = active_employees - today_present
            
            # Pending Leave Applications
            pending_leaves = LeaveApplication.objects.filter(
                user__own_user_profile__organization=organization,
                status='pending'
            ).count()
            
            # This Month Payroll
            current_month = date.today().month
            current_year = date.today().year
            monthly_payroll = PayrollRecord.objects.filter(
                organization=organization,
                payroll_month=current_month,
                payroll_year=current_year
            ).aggregate(
                total=Sum('net_salary'),
                count=Count('id')
            )
            
            return Response({
                "status": status.HTTP_200_OK,
                "message": "Dashboard data fetched successfully",
                "data": {
                    "employees": {
                        "total": total_employees,
                        "active": active_employees,
                        "inactive": inactive_employees
                    },
                    "admins": {
                        "total": total_admins,
                        "active": active_admins
                    },
                    "attendance_today": {
                        "total": today_attendance,
                        "present": today_present,
                        "absent": today_absent,
                        "attendance_rate": round((today_present / active_employees * 100) if active_employees > 0 else 0, 2)
                    },
                    "leaves": {
                        "pending": pending_leaves
                    },
                    "payroll": {
                        "month": current_month,
                        "year": current_year,
                        "total_amount": float(monthly_payroll['total'] or 0),
                        "employee_count": monthly_payroll['count'] or 0
                    }
                }
            })
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": {}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AdminDashboardAPIView(APIView):
    """Admin Dashboard Statistics"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, admin_id):
        try:
            admin = get_object_or_404(BaseUserModel, id=admin_id, role='admin')
            admin_profile = get_object_or_404(AdminProfile, user=admin)
            organization = admin_profile.organization
            
            # Employee Statistics
            total_employees = UserProfile.objects.filter(admin=admin).count()
            active_employees = UserProfile.objects.filter(
                admin=admin,
                user__is_active=True
            ).count()
            
            # Today's Attendance
            today = date.today()
            today_present = Attendance.objects.filter(
                user__own_user_profile__admin=admin,
                attendance_date=today,
                check_in_time__isnull=False
            ).count()
            
            # Pending Leave Applications
            pending_leaves = LeaveApplication.objects.filter(
                user__own_user_profile__admin=admin,
                status='pending'
            ).count()
            
            return Response({
                "status": status.HTTP_200_OK,
                "message": "Dashboard data fetched successfully",
                "data": {
                    "employees": {
                        "total": total_employees,
                        "active": active_employees
                    },
                    "attendance_today": {
                        "present": today_present,
                        "attendance_rate": round((today_present / active_employees * 100) if active_employees > 0 else 0, 2)
                    },
                    "leaves": {
                        "pending": pending_leaves
                    }
                }
            })
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": {}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

