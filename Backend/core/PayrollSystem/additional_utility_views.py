"""
Additional Utility APIs for Payroll System
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.db.models import Q, Count, Sum, Avg, Max, Min
from django.utils import timezone
from datetime import datetime, date
from decimal import Decimal

from .models import (
    PayrollRecord, EmployeeSalaryStructure, SalaryStructure,
    EmployeeAdvance, EmployeeBankInfo, PayrollSettings
)
from .serializers import (
    PayrollRecordSerializer, EmployeeSalaryStructureSerializer,
    EmployeeAdvanceSerializer, EmployeeBankInfoSerializer
)
from AuthN.models import BaseUserModel, UserProfile
from utils.pagination_utils import CustomPagination


class PayrollDashboardAPIView(APIView):
    """Payroll Dashboard Statistics"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, org_id):
        try:
            organization = get_object_or_404(BaseUserModel, id=org_id, role='organization')
            
            current_month = date.today().month
            current_year = date.today().year
            
            # Current Month Payroll
            current_payroll = PayrollRecord.objects.filter(
                organization=organization,
                payroll_month=current_month,
                payroll_year=current_year
            )
            
            total_payroll = current_payroll.aggregate(
                total_gross=Sum('gross_salary'),
                total_net=Sum('net_salary'),
                total_deductions=Sum('total_deductions'),
                count=Count('id')
            )
            
            # Pending Advances
            pending_advances = EmployeeAdvance.objects.filter(
                organization=organization,
                status='pending'
            ).aggregate(
                total=Sum('amount'),
                count=Count('id')
            )
            
            # Employees with Salary Structure
            employees_with_structure = EmployeeSalaryStructure.objects.filter(
                organization=organization,
                is_active=True
            ).count()
            
            return Response({
                "status": status.HTTP_200_OK,
                "message": "Payroll dashboard data fetched successfully",
                "data": {
                    "current_month": {
                        "month": current_month,
                        "year": current_year,
                        "total_gross": float(total_payroll['total_gross'] or 0),
                        "total_net": float(total_payroll['total_net'] or 0),
                        "total_deductions": float(total_payroll['total_deductions'] or 0),
                        "employee_count": total_payroll['count'] or 0
                    },
                    "advances": {
                        "pending_amount": float(pending_advances['total'] or 0),
                        "pending_count": pending_advances['count'] or 0
                    },
                    "structures": {
                        "employees_with_structure": employees_with_structure
                    }
                }
            })
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": {}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class EmployeePayrollHistoryAPIView(APIView):
    """Get employee payroll history"""
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination
    
    def get(self, request, org_id, employee_id):
        try:
            organization = get_object_or_404(BaseUserModel, id=org_id, role='organization')
            employee = get_object_or_404(BaseUserModel, id=employee_id, role='user')
            
            payrolls = PayrollRecord.objects.filter(
                organization=organization,
                employee=employee
            ).order_by('-payroll_year', '-payroll_month')
            
            # Filters
            year = request.query_params.get('year')
            month = request.query_params.get('month')
            
            if year:
                payrolls = payrolls.filter(payroll_year=int(year))
            if month:
                payrolls = payrolls.filter(payroll_month=int(month))
            
            paginator = self.pagination_class()
            paginated_qs = paginator.paginate_queryset(payrolls, request)
            
            serializer = PayrollRecordSerializer(paginated_qs, many=True)
            pagination_data = paginator.get_paginated_response(serializer.data)
            
            # Summary
            total_earned = payrolls.aggregate(total=Sum('net_salary'))
            
            pagination_data["summary"] = {
                "total_earned": float(total_earned['total'] or 0),
                "total_records": payrolls.count()
            }
            
            return Response({
                "status": status.HTTP_200_OK,
                "message": "Payroll history fetched successfully",
                "data": pagination_data
            })
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PayrollSummaryAPIView(APIView):
    """Get payroll summary for a period"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, org_id):
        try:
            organization = get_object_or_404(BaseUserModel, id=org_id, role='organization')
            
            month = int(request.query_params.get('month', date.today().month))
            year = int(request.query_params.get('year', date.today().year))
            
            payrolls = PayrollRecord.objects.filter(
                organization=organization,
                payroll_month=month,
                payroll_year=year
            )
            
            summary = payrolls.aggregate(
                total_gross=Sum('gross_salary'),
                total_net=Sum('net_salary'),
                total_deductions=Sum('total_deductions'),
                total_pf=Sum('pf_employee'),
                total_esi=Sum('esi_employee'),
                total_pt=Sum('professional_tax'),
                total_tds=Sum('tds'),
                avg_salary=Avg('net_salary'),
                max_salary=Max('net_salary'),
                min_salary=Min('net_salary'),
                count=Count('id')
            )
            
            return Response({
                "status": status.HTTP_200_OK,
                "message": "Payroll summary fetched successfully",
                "data": {
                    "period": {
                        "month": month,
                        "year": year
                    },
                    "summary": {
                        "total_gross": float(summary['total_gross'] or 0),
                        "total_net": float(summary['total_net'] or 0),
                        "total_deductions": float(summary['total_deductions'] or 0),
                        "total_pf": float(summary['total_pf'] or 0),
                        "total_esi": float(summary['total_esi'] or 0),
                        "total_pt": float(summary['total_pt'] or 0),
                        "total_tds": float(summary['total_tds'] or 0),
                        "average_salary": float(summary['avg_salary'] or 0),
                        "max_salary": float(summary['max_salary'] or 0),
                        "min_salary": float(summary['min_salary'] or 0),
                        "employee_count": summary['count'] or 0
                    }
                }
            })
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": {}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class EmployeeAdvanceListAPIView(APIView):
    """Get employee advances list"""
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination
    
    def get(self, request, org_id, employee_id=None):
        try:
            organization = get_object_or_404(BaseUserModel, id=org_id, role='organization')
            
            if employee_id:
                employee = get_object_or_404(BaseUserModel, id=employee_id, role='user')
                advances = EmployeeAdvance.objects.filter(
                    organization=organization,
                    employee=employee
                )
            else:
                advances = EmployeeAdvance.objects.filter(organization=organization)
            
            # Filters
            status_filter = request.query_params.get('status')
            advance_type = request.query_params.get('advance_type')
            
            if status_filter:
                advances = advances.filter(status=status_filter)
            if advance_type:
                advances = advances.filter(advance_type=advance_type)
            
            advances = advances.order_by('-advance_date')
            
            paginator = self.pagination_class()
            paginated_qs = paginator.paginate_queryset(advances, request)
            
            serializer = EmployeeAdvanceSerializer(paginated_qs, many=True)
            pagination_data = paginator.get_paginated_response(serializer.data)
            
            # Summary
            total_advances = advances.aggregate(total=Sum('amount'))
            pending_advances = advances.filter(status='pending').aggregate(total=Sum('amount'))
            
            pagination_data["summary"] = {
                "total_amount": float(total_advances['total'] or 0),
                "pending_amount": float(pending_advances['total'] or 0)
            }
            
            return Response({
                "status": status.HTTP_200_OK,
                "message": "Advances fetched successfully",
                "data": pagination_data
            })
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class EmployeeBankInfoListAPIView(APIView):
    """Get employee bank information list"""
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination
    
    def get(self, request, org_id):
        try:
            organization = get_object_or_404(BaseUserModel, id=org_id, role='organization')
            
            bank_infos = EmployeeBankInfo.objects.filter(organization=organization)
            
            search = request.query_params.get('q')
            if search:
                bank_infos = bank_infos.filter(
                    Q(employee__own_user_profile__user_name__icontains=search) |
                    Q(bank_name__icontains=search) |
                    Q(account_number__icontains=search)
                )
            
            paginator = self.pagination_class()
            paginated_qs = paginator.paginate_queryset(bank_infos, request)
            
            serializer = EmployeeBankInfoSerializer(paginated_qs, many=True)
            pagination_data = paginator.get_paginated_response(serializer.data)
            
            return Response({
                "status": status.HTTP_200_OK,
                "message": "Bank information fetched successfully",
                "data": pagination_data
            })
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

