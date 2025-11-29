"""
Additional Utility APIs for HR Analytics
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Q, Count, Sum, Avg
from django.utils import timezone
from datetime import datetime, date
from decimal import Decimal

from .models import AttendanceAnalytics, AttritionAnalytics, SalaryDistribution, CostCenterAnalytics
from .serializers import (
    AttendanceAnalyticsSerializer, AttritionAnalyticsSerializer,
    SalaryDistributionSerializer, CostCenterAnalyticsSerializer
)
from AuthN.models import BaseUserModel, UserProfile
from utils.pagination_utils import CustomPagination


class AnalyticsDashboardAPIView(APIView):
    """HR Analytics Dashboard"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, org_id):
        try:
            organization = get_object_or_404(BaseUserModel, id=org_id, role='organization')
            
            today = date.today()
            current_month = today.month
            current_year = today.year
            
            # Attendance Analytics
            attendance_analytics = AttendanceAnalytics.objects.filter(
                organization=organization,
                period_type='monthly',
                period_start__year=current_year,
                period_start__month=current_month
            ).aggregate(
                avg_attendance_rate=Avg('attendance_rate'),
                total_employees=Count('employee', distinct=True)
            )
            
            # Attrition Analytics
            attrition_analytics = AttritionAnalytics.objects.filter(
                organization=organization,
                period_type='monthly',
                period_start__year=current_year,
                period_start__month=current_month
            ).first()
            
            # Salary Distribution
            salary_dist = SalaryDistribution.objects.filter(
                organization=organization,
                period_type='monthly',
                period_start__year=current_year,
                period_start__month=current_month
            ).first()
            
            return Response({
                "status": status.HTTP_200_OK,
                "message": "Analytics dashboard data fetched successfully",
                "data": {
                    "attendance": {
                        "average_rate": round(float(attendance_analytics['avg_attendance_rate'] or 0), 2),
                        "total_employees": attendance_analytics['total_employees'] or 0
                    },
                    "attrition": {
                        "rate": round(float(attrition_analytics.attrition_rate), 2) if attrition_analytics else 0,
                        "separations": attrition_analytics.separations if attrition_analytics else 0
                    },
                    "salary": {
                        "total_payroll": float(salary_dist.total_payroll_cost) if salary_dist else 0,
                        "average_salary": float(salary_dist.average_salary) if salary_dist else 0
                    }
                }
            })
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": {}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

