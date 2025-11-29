"""
HR Analytics Views
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.db.models import Q, Count, Avg, Sum, Max, Min
from django.utils import timezone
from datetime import datetime, date, timedelta
from decimal import Decimal

from .models import (
    CostCenter, AttendanceAnalytics, AttritionRecord,
    AttritionAnalytics, SalaryDistribution, CostCenterAnalytics
)
from .serializers import (
    CostCenterSerializer, AttendanceAnalyticsSerializer, AttritionRecordSerializer,
    AttritionAnalyticsSerializer, SalaryDistributionSerializer, CostCenterAnalyticsSerializer
)
from AuthN.models import BaseUserModel, UserProfile
from WorkLog.models import Attendance
from PayrollSystem.models import PayrollRecord
from utils.pagination_utils import CustomPagination


class CostCenterAPIView(APIView):
    """Cost Center CRUD"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, org_id, pk=None):
        try:
            organization = get_object_or_404(BaseUserModel, id=org_id, role='organization')
            
            if pk:
                center = get_object_or_404(CostCenter, id=pk, organization=organization)
                serializer = CostCenterSerializer(center)
                return Response({
                    "status": status.HTTP_200_OK,
                    "message": "Cost center fetched successfully",
                    "data": serializer.data
                })
            else:
                centers = CostCenter.objects.filter(organization=organization, is_active=True)
                serializer = CostCenterSerializer(centers, many=True)
                return Response({
                    "status": status.HTTP_200_OK,
                    "message": "Cost centers fetched successfully",
                    "data": serializer.data
                })
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def post(self, request, org_id):
        try:
            organization = get_object_or_404(BaseUserModel, id=org_id, role='organization')
            
            data = request.data.copy()
            data['organization'] = str(organization.id)
            
            serializer = CostCenterSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                return Response({
                    "status": status.HTTP_201_CREATED,
                    "message": "Cost center created successfully",
                    "data": serializer.data
                }, status=status.HTTP_201_CREATED)
            return Response({
                "status": status.HTTP_400_BAD_REQUEST,
                "message": "Validation error",
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AttendanceAnalyticsAPIView(APIView):
    """Attendance Analytics"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, org_id):
        try:
            organization = get_object_or_404(BaseUserModel, id=org_id, role='organization')
            
            period_type = request.query_params.get('period_type', 'monthly')
            period_start = request.query_params.get('period_start')
            period_end = request.query_params.get('period_end')
            employee_id = request.query_params.get('employee_id')
            
            if not period_start or not period_end:
                # Default to current month
                today = date.today()
                period_start = date(today.year, today.month, 1)
                period_end = today
            
            analytics = AttendanceAnalytics.objects.filter(
                organization=organization,
                period_type=period_type,
                period_start=period_start,
                period_end=period_end
            )
            
            if employee_id:
                analytics = analytics.filter(employee_id=employee_id)
            
            serializer = AttendanceAnalyticsSerializer(analytics, many=True)
            return Response({
                "status": status.HTTP_200_OK,
                "message": "Analytics fetched successfully",
                "data": serializer.data
            })
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def post(self, request, org_id):
        """Generate/Update Attendance Analytics"""
        try:
            organization = get_object_or_404(BaseUserModel, id=org_id, role='organization')
            
            period_type = request.data.get('period_type', 'monthly')
            period_start = request.data.get('period_start')
            period_end = request.data.get('period_end')
            employee_id = request.data.get('employee_id')
            
            if not period_start or not period_end:
                return Response({
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "period_start and period_end are required"
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Generate analytics for all employees or specific employee
            if employee_id:
                employees = [get_object_or_404(BaseUserModel, id=employee_id, role='user')]
            else:
                user_profiles = UserProfile.objects.filter(organization=organization)
                employees = [profile.user for profile in user_profiles]
            
            generated_count = 0
            for employee in employees:
                # Calculate attendance metrics
                attendances = Attendance.objects.filter(
                    user=employee,
                    attendance_date__gte=period_start,
                    attendance_date__lte=period_end
                )
                
                total_days = (date.fromisoformat(str(period_end)) - date.fromisoformat(str(period_start))).days + 1
                present_days = attendances.filter(check_in_time__isnull=False).count()
                absent_days = total_days - present_days
                
                # Calculate hours
                total_working_minutes = sum([
                    a.total_working_minutes or 0 for a in attendances if a.total_working_minutes
                ])
                total_working_hours = Decimal(total_working_minutes) / Decimal('60')
                average_working_hours = total_working_hours / present_days if present_days > 0 else Decimal('0')
                
                # Calculate rates
                attendance_rate = (present_days / total_days * 100) if total_days > 0 else Decimal('0')
                
                # Get or create analytics record
                analytics, created = AttendanceAnalytics.objects.get_or_create(
                    organization=organization,
                    employee=employee,
                    period_type=period_type,
                    period_start=period_start,
                    period_end=period_end,
                    defaults={
                        'total_days': total_days,
                        'present_days': present_days,
                        'absent_days': absent_days,
                        'total_working_hours': total_working_hours,
                        'average_working_hours': average_working_hours,
                        'attendance_rate': attendance_rate
                    }
                )
                
                if not created:
                    # Update existing
                    analytics.total_days = total_days
                    analytics.present_days = present_days
                    analytics.absent_days = absent_days
                    analytics.total_working_hours = total_working_hours
                    analytics.average_working_hours = average_working_hours
                    analytics.attendance_rate = attendance_rate
                    analytics.save()
                
                generated_count += 1
            
            return Response({
                "status": status.HTTP_200_OK,
                "message": f"Analytics generated for {generated_count} employee(s)",
                "generated": generated_count
            })
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AttritionRecordAPIView(APIView):
    """Attrition Record CRUD"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, org_id, pk=None):
        try:
            organization = get_object_or_404(BaseUserModel, id=org_id, role='organization')
            
            if pk:
                record = get_object_or_404(AttritionRecord, id=pk, organization=organization)
                serializer = AttritionRecordSerializer(record)
                return Response({
                    "status": status.HTTP_200_OK,
                    "message": "Record fetched successfully",
                    "data": serializer.data
                })
            else:
                records = AttritionRecord.objects.filter(organization=organization)
                serializer = AttritionRecordSerializer(records.order_by('-separation_date'), many=True)
                return Response({
                    "status": status.HTTP_200_OK,
                    "message": "Records fetched successfully",
                    "data": serializer.data
                })
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def post(self, request, org_id):
        try:
            organization = get_object_or_404(BaseUserModel, id=org_id, role='organization')
            employee = get_object_or_404(BaseUserModel, id=request.data.get('employee_id'), role='user')
            
            # Get employee profile for tenure calculation
            try:
                profile = UserProfile.objects.get(user=employee)
                if profile.date_of_joining:
                    separation_date = date.fromisoformat(str(request.data.get('separation_date')))
                    tenure_days = (separation_date - profile.date_of_joining).days
                    tenure_months = tenure_days // 30
                else:
                    tenure_months = 0
            except:
                tenure_months = 0
            
            data = request.data.copy()
            data['organization'] = str(organization.id)
            data['employee'] = str(employee.id)
            data['tenure_months'] = tenure_months
            
            serializer = AttritionRecordSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                return Response({
                    "status": status.HTTP_201_CREATED,
                    "message": "Attrition record created successfully",
                    "data": serializer.data
                }, status=status.HTTP_201_CREATED)
            return Response({
                "status": status.HTTP_400_BAD_REQUEST,
                "message": "Validation error",
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SalaryDistributionAPIView(APIView):
    """Salary Distribution Analytics"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, org_id):
        try:
            organization = get_object_or_404(BaseUserModel, id=org_id, role='organization')
            
            period_type = request.query_params.get('period_type', 'monthly')
            period_start = request.query_params.get('period_start')
            period_end = request.query_params.get('period_end')
            
            if not period_start or not period_end:
                today = date.today()
                period_start = date(today.year, today.month, 1)
                period_end = today
            
            distributions = SalaryDistribution.objects.filter(
                organization=organization,
                period_type=period_type,
                period_start=period_start,
                period_end=period_end
            )
            
            serializer = SalaryDistributionSerializer(distributions, many=True)
            return Response({
                "status": status.HTTP_200_OK,
                "message": "Salary distributions fetched successfully",
                "data": serializer.data
            })
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def post(self, request, org_id):
        """Generate Salary Distribution Analytics"""
        try:
            organization = get_object_or_404(BaseUserModel, id=org_id, role='organization')
            
            period_type = request.data.get('period_type', 'monthly')
            period_start = request.data.get('period_start')
            period_end = request.data.get('period_end')
            month = request.data.get('month')
            year = request.data.get('year', date.today().year)
            
            if not period_start or not period_end:
                if month:
                    period_start = date(year, month, 1)
                    # Last day of month
                    if month == 12:
                        period_end = date(year + 1, 1, 1) - timedelta(days=1)
                    else:
                        period_end = date(year, month + 1, 1) - timedelta(days=1)
                else:
                    period_start = date(year, 1, 1)
                    period_end = date(year, 12, 31)
            
            # Get payroll records for the period
            payroll_records = PayrollRecord.objects.filter(
                organization=organization,
                payroll_year=year
            )
            
            if month:
                payroll_records = payroll_records.filter(payroll_month=month)
            
            if not payroll_records.exists():
                return Response({
                    "status": status.HTTP_404_NOT_FOUND,
                    "message": "No payroll records found for the specified period"
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Calculate statistics
            salaries = [record.net_salary for record in payroll_records if record.net_salary]
            if not salaries:
                return Response({
                    "status": status.HTTP_404_NOT_FOUND,
                    "message": "No salary data found"
                }, status=status.HTTP_404_NOT_FOUND)
            
            total_payroll = sum(salaries)
            average_salary = total_payroll / len(salaries)
            sorted_salaries = sorted(salaries)
            median_salary = sorted_salaries[len(sorted_salaries) // 2] if sorted_salaries else Decimal('0')
            min_salary = min(salaries)
            max_salary = max(salaries)
            
            # Get or create distribution
            distribution, created = SalaryDistribution.objects.get_or_create(
                organization=organization,
                period_type=period_type,
                period_start=period_start,
                period_end=period_end,
                defaults={
                    'total_payroll_cost': total_payroll,
                    'average_salary': average_salary,
                    'median_salary': median_salary,
                    'min_salary': min_salary,
                    'max_salary': max_salary
                }
            )
            
            if not created:
                distribution.total_payroll_cost = total_payroll
                distribution.average_salary = average_salary
                distribution.median_salary = median_salary
                distribution.min_salary = min_salary
                distribution.max_salary = max_salary
                distribution.save()
            
            serializer = SalaryDistributionSerializer(distribution)
            return Response({
                "status": status.HTTP_200_OK,
                "message": "Salary distribution generated successfully",
                "data": serializer.data
            })
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

