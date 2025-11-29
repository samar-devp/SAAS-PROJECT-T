"""
Comprehensive Indian Payroll System Views
All payroll operations: generation, reports, management
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.db.models import Q, Sum, Count
from django.utils import timezone
from datetime import datetime, date
from decimal import Decimal
import traceback

from .models import (
    SalaryComponent, SalaryStructure, StructureComponent,
    EmployeeSalaryStructure, EmployeeSalaryComponent,
    EmployeeBankInfo, PayrollSettings, EmployeeAdvance,
    PayrollRecord, PayrollComponentEntry,
    ProfessionalTaxSlab, TDSSlab
)
from .serializers import (
    SalaryComponentSerializer, SalaryStructureSerializer,
    StructureComponentSerializer, EmployeeSalaryStructureSerializer,
    EmployeeSalaryComponentSerializer, EmployeeBankInfoSerializer,
    PayrollSettingsSerializer, EmployeeAdvanceSerializer,
    PayrollRecordSerializer, ProfessionalTaxSlabSerializer,
    TDSSlabSerializer
)
from .payroll_calculator import PayrollCalculator
from .payroll_excel_service import PayrollExcelService
from .additional_views import (
    UpdatePayrollReportView, BIPayrollReportView, PayrollDownloadInfo,
    DownloadAdvanceIncomeTaxSampleExcel, DownloadDeductionSampleExcel,
    DownloadEarningSampleExcel, UploadAdvanceIncomeTaxExcel,
    UploadDeductionExcel, UploadEarningExcel,
    GenerateCustomPayableSheet, EmployeePayslipAPI
)
from AuthN.models import BaseUserModel, UserProfile
from utils.pagination_utils import CustomPagination
import openpyxl
from io import BytesIO


# ==================== SALARY STRUCTURE CRUD ====================

class SalaryStructureCRUD(APIView):
    """CRUD operations for Salary Structure"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, org_id, id=None):
        """Get salary structure(s)"""
        try:
            organization = get_object_or_404(BaseUserModel, id=org_id, role='organization')
            
            if id:
                structure = get_object_or_404(SalaryStructure, id=id, organization=organization)
                serializer = SalaryStructureSerializer(structure)
                return Response({
                    "status": status.HTTP_200_OK,
                    "message": "Salary structure fetched successfully",
                    "data": serializer.data
                })
            else:
                structures = SalaryStructure.objects.filter(organization=organization)
                serializer = SalaryStructureSerializer(structures, many=True)
                return Response({
                    "status": status.HTTP_200_OK,
                    "message": "Salary structures fetched successfully",
                    "data": serializer.data
                })
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def post(self, request, org_id):
        """Create salary structure"""
        try:
            organization = get_object_or_404(BaseUserModel, id=org_id, role='organization')
            data = request.data.copy()
            data['organization'] = str(organization.id)
            data['created_by'] = str(request.user.id) if request.user.role == 'admin' else None
            
            serializer = SalaryStructureSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                return Response({
                    "status": status.HTTP_201_CREATED,
                    "message": "Salary structure created successfully",
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
    
    def put(self, request, org_id, id):
        """Update salary structure"""
        try:
            organization = get_object_or_404(BaseUserModel, id=org_id, role='organization')
            structure = get_object_or_404(SalaryStructure, id=id, organization=organization)
            
            serializer = SalaryStructureSerializer(structure, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({
                    "status": status.HTTP_200_OK,
                    "message": "Salary structure updated successfully",
                    "data": serializer.data
                })
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
    
    def delete(self, request, org_id, id):
        """Delete salary structure"""
        try:
            organization = get_object_or_404(BaseUserModel, id=org_id, role='organization')
            structure = get_object_or_404(SalaryStructure, id=id, organization=organization)
            structure.delete()
            return Response({
                "status": status.HTTP_200_OK,
                "message": "Salary structure deleted successfully"
            })
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==================== EMPLOYEE ASSIGNED STRUCTURE ====================

class EmployeeAssignStructure(APIView):
    """Assign salary structure to employee"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request, org_id):
        """Assign structure to employee"""
        try:
            organization = get_object_or_404(BaseUserModel, id=org_id, role='organization')
            employee_id = request.data.get('employee_id')
            structure_id = request.data.get('structure_id')
            effective_from = request.data.get('effective_from', date.today().isoformat())
            
            employee = get_object_or_404(BaseUserModel, id=employee_id, role='user')
            structure = get_object_or_404(SalaryStructure, id=structure_id, organization=organization)
            
            # Deactivate previous assignments
            EmployeeSalaryStructure.objects.filter(
                employee=employee,
                is_active=True
            ).update(is_active=False, effective_to=effective_from)
            
            # Create new assignment
            assignment = EmployeeSalaryStructure.objects.create(
                employee=employee,
                structure=structure,
                effective_from=effective_from,
                assigned_by=request.user if request.user.role == 'admin' else None,
                is_active=True
            )
            
            serializer = EmployeeSalaryStructureSerializer(assignment)
            return Response({
                "status": status.HTTP_201_CREATED,
                "message": "Salary structure assigned successfully",
                "data": serializer.data
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==================== EMPLOYEE ASSIGNED PAY ====================

class EmployeeAssignPay(APIView):
    """Assign custom pay components to employee"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request, org_id):
        """Assign pay components"""
        try:
            organization = get_object_or_404(BaseUserModel, id=org_id, role='organization')
            employee_id = request.data.get('employee_id')
            components = request.data.get('components', [])
            effective_from = request.data.get('effective_from', date.today().isoformat())
            
            employee = get_object_or_404(BaseUserModel, id=employee_id, role='user')
            
            created_components = []
            for comp_data in components:
                component_id = comp_data.get('component_id')
                amount = comp_data.get('amount')
                
                component = get_object_or_404(
                    SalaryComponent,
                    id=component_id,
                    organization=organization
                )
                
                # Deactivate previous
                EmployeeSalaryComponent.objects.filter(
                    employee=employee,
                    component=component,
                    is_active=True
                ).update(is_active=False, effective_to=effective_from)
                
                # Create new
                emp_comp = EmployeeSalaryComponent.objects.create(
                    employee=employee,
                    component=component,
                    amount=amount,
                    effective_from=effective_from,
                    is_active=True
                )
                created_components.append(emp_comp)
            
            serializer = EmployeeSalaryComponentSerializer(created_components, many=True)
            return Response({
                "status": status.HTTP_201_CREATED,
                "message": "Pay components assigned successfully",
                "data": serializer.data
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==================== GET ASSIGNED STRUCTURE ====================

class GetAssignStructure(APIView):
    """Get assigned structure for employee(s)"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, admin_id, emp_id=None):
        """Get assigned structures"""
        try:
            admin = get_object_or_404(BaseUserModel, id=admin_id, role='admin')
            
            if emp_id:
                employee = get_object_or_404(BaseUserModel, id=emp_id, role='user')
                assignments = EmployeeSalaryStructure.objects.filter(
                    employee=employee,
                    is_active=True
                )
            else:
                # Get all employees under admin
                user_profiles = UserProfile.objects.filter(admin=admin)
                employee_ids = [profile.user.id for profile in user_profiles]
                assignments = EmployeeSalaryStructure.objects.filter(
                    employee_id__in=employee_ids,
                    is_active=True
                )
            
            serializer = EmployeeSalaryStructureSerializer(assignments, many=True)
            return Response({
                "status": status.HTTP_200_OK,
                "message": "Assigned structures fetched successfully",
                "data": serializer.data
            })
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==================== ADVANCE FORM ====================

class AdvanceFormAPIView(APIView):
    """Advance/Loan management"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, admin_id, emp_id=None):
        """Get advances"""
        try:
            admin = get_object_or_404(BaseUserModel, id=admin_id, role='admin')
            
            if emp_id:
                employee = get_object_or_404(BaseUserModel, id=emp_id, role='user')
                advances = EmployeeAdvance.objects.filter(employee=employee, admin=admin)
            else:
                advances = EmployeeAdvance.objects.filter(admin=admin)
            
            serializer = EmployeeAdvanceSerializer(advances, many=True)
            return Response({
                "status": status.HTTP_200_OK,
                "message": "Advances fetched successfully",
                "data": serializer.data
            })
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def post(self, request, admin_id, emp_id=None):
        """Create advance"""
        try:
            admin = get_object_or_404(BaseUserModel, id=admin_id, role='admin')
            employee_id = emp_id or request.data.get('employee_id')
            employee = get_object_or_404(BaseUserModel, id=employee_id, role='user')
            
            data = request.data.copy()
            data['employee'] = str(employee.id)
            data['admin'] = str(admin.id)
            data['remaining_amount'] = data.get('amount', 0)
            
            serializer = EmployeeAdvanceSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                return Response({
                    "status": status.HTTP_201_CREATED,
                    "message": "Advance created successfully",
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
    
    def put(self, request, admin_id, emp_id):
        """Update advance status"""
        try:
            advance_id = request.data.get('advance_id')
            advance = get_object_or_404(EmployeeAdvance, id=advance_id, admin_id=admin_id)
            
            serializer = EmployeeAdvanceSerializer(advance, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({
                    "status": status.HTTP_200_OK,
                    "message": "Advance updated successfully",
                    "data": serializer.data
                })
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


# ==================== EMPLOYEE BANK INFO ====================

class EmployeeBankInfoAPIView(APIView):
    """Employee bank information"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, admin_id, emp_id=None):
        """Get bank info"""
        try:
            if emp_id:
                employee = get_object_or_404(BaseUserModel, id=emp_id, role='user')
                try:
                    bank_info = EmployeeBankInfo.objects.get(employee=employee)
                    serializer = EmployeeBankInfoSerializer(bank_info)
                    return Response({
                        "status": status.HTTP_200_OK,
                        "message": "Bank info fetched successfully",
                        "data": [serializer.data]
                    })
                except EmployeeBankInfo.DoesNotExist:
                    return Response({
                        "status": status.HTTP_404_NOT_FOUND,
                        "message": "Bank info not found",
                        "data": []
                    })
            else:
                # Get all employees under admin
                user_profiles = UserProfile.objects.filter(admin_id=admin_id)
                employee_ids = [profile.user.id for profile in user_profiles]
                bank_infos = EmployeeBankInfo.objects.filter(employee_id__in=employee_ids)
                serializer = EmployeeBankInfoSerializer(bank_infos, many=True)
                return Response({
                    "status": status.HTTP_200_OK,
                    "message": "Bank info fetched successfully",
                    "data": serializer.data
                })
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def post(self, request, admin_id, emp_id=None):
        """Create/Update bank info"""
        try:
            employee_id = emp_id or request.data.get('employee_id')
            employee = get_object_or_404(BaseUserModel, id=employee_id, role='user')
            
            bank_info, created = EmployeeBankInfo.objects.update_or_create(
                employee=employee,
                defaults=request.data
            )
            
            serializer = EmployeeBankInfoSerializer(bank_info)
            message = "Bank info created successfully" if created else "Bank info updated successfully"
            return Response({
                "status": status.HTTP_200_OK,
                "message": message,
                "data": serializer.data
            })
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==================== PAYROLL GENERATION ====================

class GeneratePayrollAPIView(APIView):
    """Generate payroll for employees"""
    permission_classes = [IsAuthenticated]
    
    @transaction.atomic
    def post(self, request, org_id):
        """Generate payroll for month/year"""
        try:
            organization = get_object_or_404(BaseUserModel, id=org_id, role='organization')
            month = int(request.data.get('month'))
            year = int(request.data.get('year'))
            employee_ids = request.data.get('employee_ids', [])  # Optional: specific employees
            admin_id = request.data.get('admin_id')
            
            admin = None
            if admin_id:
                admin = get_object_or_404(BaseUserModel, id=admin_id, role='admin')
            
            payroll_date = date(year, month, 1)
            
            # Get employees
            if employee_ids:
                employees = BaseUserModel.objects.filter(
                    id__in=employee_ids,
                    role='user'
                )
            elif admin:
                user_profiles = UserProfile.objects.filter(admin=admin)
                employees = [profile.user for profile in user_profiles]
            else:
                user_profiles = UserProfile.objects.filter(
                    organization=organization
                )
                employees = [profile.user for profile in user_profiles]
            
            generated_payrolls = []
            errors = []
            
            for employee in employees:
                try:
                    # Check if payroll already exists
                    existing = PayrollRecord.objects.filter(
                        employee=employee,
                        payroll_month=month,
                        payroll_year=year
                    ).first()
                    
                    if existing:
                        errors.append(f"Payroll already exists for {employee.email}")
                        continue
                    
                    # Calculate payroll
                    calculator = PayrollCalculator(employee, month, year, admin, organization)
                    payroll_data = calculator.calculate_payroll()
                    
                    # Get employee's admin and organization
                    user_profile = employee.own_user_profile
                    emp_admin = user_profile.admin
                    emp_org = user_profile.organization
                    
                    # Create payroll record with enhanced attendance data
                    attendance_data = payroll_data['attendance_data']
                    payroll_record = PayrollRecord.objects.create(
                        employee=employee,
                        admin=emp_admin,
                        organization=emp_org,
                        payroll_month=month,
                        payroll_year=year,
                        payroll_date=payroll_date,
                        total_days=attendance_data.get('total_days', 0),
                        present_days=attendance_data.get('present_days', 0),
                        absent_days=attendance_data.get('absent_days', 0),
                        leave_days=attendance_data.get('leave_days', 0),
                        working_days=attendance_data.get('working_days', 0),
                        overtime_hours=attendance_data.get('overtime_hours', 0),
                        basic_salary=payroll_data['earnings'].get('BASIC', {}).get('amount', 0),
                        hra=payroll_data['earnings'].get('HRA', {}).get('amount', 0),
                        special_allowance=payroll_data['earnings'].get('SPECIAL_ALLOWANCE', {}).get('amount', 0),
                        overtime_amount=payroll_data['earnings'].get('OVERTIME', {}).get('amount', 0),
                        gross_salary=payroll_data['gross_salary'],
                        pf_employee=payroll_data['deductions'].get('PF_EMPLOYEE', {}).get('amount', 0),
                        esi_employee=payroll_data['deductions'].get('ESI_EMPLOYEE', {}).get('amount', 0),
                        professional_tax=payroll_data['deductions'].get('PROFESSIONAL_TAX', {}).get('amount', 0),
                        tds=payroll_data['deductions'].get('TDS', {}).get('amount', 0),
                        advance_deduction=payroll_data['deductions'].get('ADVANCE', {}).get('amount', 0),
                        loan_deduction=payroll_data['deductions'].get('LOAN', {}).get('amount', 0),
                        total_deductions=payroll_data['total_deductions'],
                        net_salary=payroll_data['net_salary'],
                        earnings_breakdown={
                            **payroll_data['earnings'],
                            'calculation_summary': payroll_data.get('calculation_summary', {})
                        },
                        deductions_breakdown={
                            **payroll_data['deductions'],
                            'attendance_details': {
                                'leave_days': attendance_data.get('leave_days', 0),
                                'lop_days': attendance_data.get('lop_days', 0),
                                'half_day_leaves': attendance_data.get('half_day_leaves', 0),
                                'week_off_days': attendance_data.get('week_off_days', 0),
                                'holiday_days': attendance_data.get('holiday_days', 0),
                                'sandwich_absent_days': attendance_data.get('sandwich_absent_days', 0),
                                'payable_days': attendance_data.get('payable_days', 0),
                                'late_days': attendance_data.get('late_days', 0),
                                'early_exit_days': attendance_data.get('early_exit_days', 0),
                                'total_late_minutes': attendance_data.get('total_late_minutes', 0),
                                'total_early_exit_minutes': attendance_data.get('total_early_exit_minutes', 0)
                            }
                        },
                        status='processed',
                        created_by=request.user
                    )
                    
                    # Create component entries
                    for code, comp_data in payroll_data['earnings'].items():
                        try:
                            component = SalaryComponent.objects.get(
                                code=code,
                                organization=organization
                            )
                            PayrollComponentEntry.objects.create(
                                payroll=payroll_record,
                                component=component,
                                amount=comp_data['amount'],
                                is_earning=True
                            )
                        except SalaryComponent.DoesNotExist:
                            pass
                    
                    for code, comp_data in payroll_data['deductions'].items():
                        try:
                            component = SalaryComponent.objects.get(
                                code=code,
                                organization=organization
                            )
                            PayrollComponentEntry.objects.create(
                                payroll=payroll_record,
                                component=component,
                                amount=comp_data['amount'],
                                is_earning=False
                            )
                        except SalaryComponent.DoesNotExist:
                            pass
                    
                    generated_payrolls.append(payroll_record)
                    
                except Exception as e:
                    errors.append(f"Error for {employee.email}: {str(e)}")
                    continue
            
            serializer = PayrollRecordSerializer(generated_payrolls, many=True)
            return Response({
                "status": status.HTTP_200_OK,
                "message": f"Payroll generated for {len(generated_payrolls)} employees",
                "data": serializer.data,
                "errors": errors if errors else None
            })
            
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "line_number": traceback.extract_tb(e.__traceback__)[-1].lineno if e.__traceback__ else None,
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==================== PAYROLL MONTHLY REPORT ====================

class PayrollMonthlyReport(APIView):
    """Get monthly payroll report"""
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination
    
    def get(self, request, org_id, month, year, admin_id=None):
        """Get payroll report for month"""
        try:
            organization = get_object_or_404(BaseUserModel, id=org_id, role='organization')
            
            queryset = PayrollRecord.objects.filter(
                organization=organization,
                payroll_month=month,
                payroll_year=year
            )
            
            if admin_id:
                admin = get_object_or_404(BaseUserModel, id=admin_id, role='admin')
                queryset = queryset.filter(admin=admin)
            
            # Pagination
            paginator = self.pagination_class()
            paginated_qs = paginator.paginate_queryset(queryset, request)
            
            serializer = PayrollRecordSerializer(paginated_qs, many=True)
            pagination_data = paginator.get_paginated_response(serializer.data)
            pagination_data["results"] = serializer.data
            
            # Summary
            summary = queryset.aggregate(
                total_employees=Count('id'),
                total_gross=Sum('gross_salary'),
                total_deductions=Sum('total_deductions'),
                total_net=Sum('net_salary'),
                total_pf=Sum('pf_employee'),
                total_esi=Sum('esi_employee'),
                total_tds=Sum('tds')
            )
            
            pagination_data["summary"] = summary
            pagination_data["message"] = "Payroll report fetched successfully"
            
            return Response(pagination_data)
            
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==================== PAYROLL COMPONENTS ====================

class PayrollComponentsAPIView(APIView):
    """Manage payroll components"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, org_id):
        """Get all components"""
        try:
            organization = get_object_or_404(BaseUserModel, id=org_id, role='organization')
            components = SalaryComponent.objects.filter(organization=organization, is_active=True)
            serializer = SalaryComponentSerializer(components, many=True)
            return Response({
                "status": status.HTTP_200_OK,
                "message": "Components fetched successfully",
                "data": serializer.data
            })
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def post(self, request, org_id):
        """Create component"""
        try:
            organization = get_object_or_404(BaseUserModel, id=org_id, role='organization')
            data = request.data.copy()
            data['organization'] = str(organization.id)
            
            serializer = SalaryComponentSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                return Response({
                    "status": status.HTTP_201_CREATED,
                    "message": "Component created successfully",
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


# ==================== PAYROLL SETTINGS ====================

class PayrollSettingsAPIView(APIView):
    """Manage payroll settings"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, org_id, admin_id=None, pk=None):
        """Get settings"""
        try:
            organization = get_object_or_404(BaseUserModel, id=org_id, role='organization')
            
            if pk:
                settings = get_object_or_404(PayrollSettings, id=pk, organization=organization)
                serializer = PayrollSettingsSerializer(settings)
                return Response({
                    "status": status.HTTP_200_OK,
                    "message": "Settings fetched successfully",
                    "data": serializer.data
                })
            else:
                if admin_id:
                    admin = get_object_or_404(BaseUserModel, id=admin_id, role='admin')
                    settings = PayrollSettings.objects.filter(organization=organization, admin=admin)
                else:
                    settings = PayrollSettings.objects.filter(organization=organization)
                
                serializer = PayrollSettingsSerializer(settings, many=True)
                return Response({
                    "status": status.HTTP_200_OK,
                    "message": "Settings fetched successfully",
                    "data": serializer.data
                })
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def post(self, request, org_id, admin_id=None):
        """Create/Update settings"""
        try:
            organization = get_object_or_404(BaseUserModel, id=org_id, role='organization')
            admin = None
            if admin_id:
                admin = get_object_or_404(BaseUserModel, id=admin_id, role='admin')
            
            data = request.data.copy()
            data['organization'] = str(organization.id)
            if admin:
                data['admin'] = str(admin.id)
            
            settings, created = PayrollSettings.objects.update_or_create(
                organization=organization,
                admin=admin,
                defaults=data
            )
            
            serializer = PayrollSettingsSerializer(settings)
            message = "Settings created successfully" if created else "Settings updated successfully"
            return Response({
                "status": status.HTTP_200_OK,
                "message": message,
                "data": serializer.data
            })
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def put(self, request, org_id, admin_id, pk):
        """Update settings"""
        try:
            settings = get_object_or_404(PayrollSettings, id=pk, organization_id=org_id)
            serializer = PayrollSettingsSerializer(settings, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({
                    "status": status.HTTP_200_OK,
                    "message": "Settings updated successfully",
                    "data": serializer.data
                })
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
