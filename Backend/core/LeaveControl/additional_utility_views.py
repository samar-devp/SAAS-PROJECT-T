"""
Additional Utility APIs for Leave Management
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

from .models import (
    LeaveType, LeaveApplication, EmployeeLeaveBalance,
    LeavePolicy, CompensatoryOff, LeaveEncashment
)
from .serializers import (
    LeaveTypeSerializer, LeaveApplicationSerializer,
    EmployeeLeaveBalanceSerializer
)
from AuthN.models import BaseUserModel, UserProfile
from utils.pagination_utils import CustomPagination


class LeaveDashboardAPIView(APIView):
    """Leave Dashboard Statistics"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, org_id):
        try:
            organization = get_object_or_404(BaseUserModel, id=org_id, role='organization')
            
            # Pending Applications
            pending = LeaveApplication.objects.filter(
                user__own_user_profile__organization=organization,
                status='pending'
            ).count()
            
            # Approved This Month
            current_month = date.today().month
            current_year = date.today().year
            approved_this_month = LeaveApplication.objects.filter(
                user__own_user_profile__organization=organization,
                status='approved',
                applied_at__month=current_month,
                applied_at__year=current_year
            ).count()
            
            # Rejected This Month
            rejected_this_month = LeaveApplication.objects.filter(
                user__own_user_profile__organization=organization,
                status='rejected',
                applied_at__month=current_month,
                applied_at__year=current_year
            ).count()
            
            # Leave Types Count
            leave_types_count = LeaveType.objects.filter(
                organization=organization,
                is_active=True
            ).count()
            
            return Response({
                "status": status.HTTP_200_OK,
                "message": "Leave dashboard data fetched successfully",
                "data": {
                    "pending_applications": pending,
                    "approved_this_month": approved_this_month,
                    "rejected_this_month": rejected_this_month,
                    "leave_types": leave_types_count
                }
            })
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": {}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class EmployeeLeaveBalanceListAPIView(APIView):
    """Get employee leave balances"""
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination
    
    def get(self, request, org_id, employee_id=None):
        try:
            organization = get_object_or_404(BaseUserModel, id=org_id, role='organization')
            
            if employee_id:
                employee = get_object_or_404(BaseUserModel, id=employee_id, role='user')
                balances = EmployeeLeaveBalance.objects.filter(
                    user=employee,
                    is_active=True
                )
            else:
                user_profiles = UserProfile.objects.filter(organization=organization)
                employee_ids = [p.user.id for p in user_profiles]
                balances = EmployeeLeaveBalance.objects.filter(
                    user_id__in=employee_ids,
                    is_active=True
                )
            
            year = request.query_params.get('year', date.today().year)
            balances = balances.filter(year=int(year))
            
            paginator = self.pagination_class()
            paginated_qs = paginator.paginate_queryset(balances, request)
            
            serializer = EmployeeLeaveBalanceSerializer(paginated_qs, many=True)
            pagination_data = paginator.get_paginated_response(serializer.data)
            
            return Response({
                "status": status.HTTP_200_OK,
                "message": "Leave balances fetched successfully",
                "data": pagination_data
            })
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class LeaveApplicationListAPIView(APIView):
    """Get leave applications list with filters"""
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination
    
    def get(self, request, org_id):
        try:
            organization = get_object_or_404(BaseUserModel, id=org_id, role='organization')
            
            user_profiles = UserProfile.objects.filter(organization=organization)
            employee_ids = [p.user.id for p in user_profiles]
            
            applications = LeaveApplication.objects.filter(user_id__in=employee_ids)
            
            # Filters
            status_filter = request.query_params.get('status')
            leave_type_id = request.query_params.get('leave_type_id')
            employee_id = request.query_params.get('employee_id')
            from_date = request.query_params.get('from_date')
            to_date = request.query_params.get('to_date')
            
            if status_filter:
                applications = applications.filter(status=status_filter)
            if leave_type_id:
                applications = applications.filter(leave_type_id=leave_type_id)
            if employee_id:
                applications = applications.filter(user_id=employee_id)
            if from_date:
                applications = applications.filter(from_date__gte=from_date)
            if to_date:
                applications = applications.filter(to_date__lte=to_date)
            
            applications = applications.order_by('-applied_at')
            
            paginator = self.pagination_class()
            paginated_qs = paginator.paginate_queryset(applications, request)
            
            serializer = LeaveApplicationSerializer(paginated_qs, many=True)
            pagination_data = paginator.get_paginated_response(serializer.data)
            
            # Summary
            summary = {
                "total": applications.count(),
                "pending": applications.filter(status='pending').count(),
                "approved": applications.filter(status='approved').count(),
                "rejected": applications.filter(status='rejected').count()
            }
            
            pagination_data["summary"] = summary
            
            return Response({
                "status": status.HTTP_200_OK,
                "message": "Leave applications fetched successfully",
                "data": pagination_data
            })
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

