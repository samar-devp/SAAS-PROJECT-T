"""
Advanced Leave Management Views
Comprehensive leave operations: applications, approvals, encashment, comp-off, etc.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.db.models import Q, Sum, Count, Avg
from django.utils import timezone
from datetime import datetime, date, timedelta
from decimal import Decimal
import traceback

from .models import (
    LeaveType, LeavePolicy, EmployeeLeaveBalance, LeaveApplication,
    CompensatoryOff, LeaveEncashment, LeaveBalanceAdjustment,
    LeaveAccrualLog, LeaveApprovalDelegation, LeaveCalendarEvent
)
from .serializers import (
    LeaveTypeSerializer, LeavePolicySerializer, EmployeeLeaveBalanceSerializer,
    LeaveApplicationSerializer, CompensatoryOffSerializer, LeaveEncashmentSerializer,
    LeaveBalanceAdjustmentSerializer, LeaveAccrualLogSerializer,
    LeaveApprovalDelegationSerializer, LeaveCalendarEventSerializer
)
from .leave_calculator import LeaveCalculator
from AuthN.models import BaseUserModel, UserProfile, AdminProfile
from utils.pagination_utils import CustomPagination


# ==================== LEAVE POLICY MANAGEMENT ====================

class LeavePolicyAPIView(APIView):
    """Leave Policy CRUD - Uses admin_id to get organization"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, admin_id, pk=None):
        """Get leave policies"""
        try:
            # Get admin profile and extract organization
            admin_profile = get_object_or_404(AdminProfile, user_id=admin_id)
            organization = admin_profile.organization
            
            if pk:
                policy = get_object_or_404(LeavePolicy, id=pk, organization=organization)
                serializer = LeavePolicySerializer(policy)
                return Response({
                    "status": status.HTTP_200_OK,
                    "message": "Leave policy fetched successfully",
                    "data": serializer.data
                })
            else:
                policies = LeavePolicy.objects.filter(organization=organization, is_active=True)
                serializer = LeavePolicySerializer(policies, many=True)
                return Response({
                    "status": status.HTTP_200_OK,
                    "message": "Leave policies fetched successfully",
                    "data": serializer.data
                })
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def post(self, request, admin_id):
        """Create leave policy"""
        try:
            # Get admin profile and extract organization
            admin_profile = get_object_or_404(AdminProfile, user_id=admin_id)
            organization = admin_profile.organization
            
            data = request.data.copy()
            data['organization'] = str(organization.id)
            data['admin'] = str(admin_id)
            data['created_by'] = str(request.user.id) if request.user.role == 'admin' else None
            
            serializer = LeavePolicySerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                return Response({
                    "status": status.HTTP_201_CREATED,
                    "message": "Leave policy created successfully",
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
    
    def put(self, request, admin_id, pk):
        """Update leave policy"""
        try:
            # Get admin profile and extract organization
            admin_profile = get_object_or_404(AdminProfile, user_id=admin_id)
            organization = admin_profile.organization
            
            policy = get_object_or_404(LeavePolicy, id=pk, organization=organization)
            serializer = LeavePolicySerializer(policy, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({
                    "status": status.HTTP_200_OK,
                    "message": "Leave policy updated successfully",
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


# ==================== ADVANCED LEAVE APPLICATION ====================

class AdvancedLeaveApplicationAPIView(APIView):
    """Advanced Leave Application with validations"""
    permission_classes = [IsAuthenticated]
    
    @transaction.atomic
    def post(self, request, user_id):
        """Create leave application with validations"""
        try:
            user = get_object_or_404(BaseUserModel, id=user_id, role='user')
            user_profile = user.own_user_profile
            data = request.data.copy()
            
            from_date = datetime.strptime(data.get('from_date'), '%Y-%m-%d').date()
            to_date = datetime.strptime(data.get('to_date'), '%Y-%m-%d').date()
            leave_type_id = data.get('leave_type')
            
            leave_type = get_object_or_404(LeaveType, id=leave_type_id)
            
            # Calculate leave days
            calculator = LeaveCalculator(user, leave_type, from_date.year)
            availability = calculator.check_leave_availability(from_date, to_date)
            
            if not availability['available']:
                return Response({
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": availability['message'],
                    "data": availability
                }, status=status.HTTP_400_BAD_REQUEST)
            
            total_days = availability['total_days']
            
            # Create application
            data['user'] = str(user.id)
            data['admin'] = str(user_profile.admin.id)
            data['organization'] = str(user_profile.organization.id)
            data['total_days'] = float(total_days)
            data['status'] = 'pending'
            data['balance_before'] = float(availability['available_balance'])
            data['balance_after'] = float(availability['available_balance'] - total_days)
            
            serializer = LeaveApplicationSerializer(data=data)
            if serializer.is_valid():
                application = serializer.save()
                
                # Update pending balance
                balance = calculator.get_leave_balance()
                balance.pending += total_days
                balance.save()
                
                # Create calendar event
                LeaveCalendarEvent.objects.create(
                    leave_application=application,
                    user=user,
                    event_date=from_date,
                    is_full_day=(data.get('duration_type') == 'full_day'),
                    title=f"{leave_type.name} - {user_profile.user_name}",
                    color=leave_type.color_code
                )
                
                return Response({
                    "status": status.HTTP_201_CREATED,
                    "message": "Leave application created successfully",
                    "data": LeaveApplicationSerializer(application).data
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
                "line_number": traceback.extract_tb(e.__traceback__)[-1].lineno if e.__traceback__ else None,
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==================== LEAVE APPROVAL ====================

class LeaveApprovalAPIView(APIView):
    """Leave Approval/Rejection"""
    permission_classes = [IsAuthenticated]
    
    @transaction.atomic
    def post(self, request, application_id):
        """Approve or reject leave"""
        try:
            application = get_object_or_404(LeaveApplication, id=application_id)
            action = request.data.get('action')  # 'approve' or 'reject'
            comments = request.data.get('comments', '')
            
            if application.status not in ['pending', 'draft']:
                return Response({
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": f"Leave application is already {application.status}"
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if action == 'approve':
                application.status = 'approved'
                application.reviewed_by = request.user
                application.reviewed_at = timezone.now()
                application.comments = comments
                application.save()
                
                # Update balance
                calculator = LeaveCalculator(application.user, application.leave_type, application.from_date.year)
                balance = calculator.get_leave_balance()
                balance.pending -= application.total_days
                balance.used += application.total_days
                balance.save()
                
                return Response({
                    "status": status.HTTP_200_OK,
                    "message": "Leave approved successfully",
                    "data": LeaveApplicationSerializer(application).data
                })
            
            elif action == 'reject':
                application.status = 'rejected'
                application.reviewed_by = request.user
                application.reviewed_at = timezone.now()
                application.rejection_reason = comments
                application.comments = comments
                application.save()
                
                # Revert pending balance
                calculator = LeaveCalculator(application.user, application.leave_type, application.from_date.year)
                balance = calculator.get_leave_balance()
                balance.pending -= application.total_days
                balance.save()
                
                return Response({
                    "status": status.HTTP_200_OK,
                    "message": "Leave rejected",
                    "data": LeaveApplicationSerializer(application).data
                })
            
            else:
                return Response({
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Invalid action. Use 'approve' or 'reject'"
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==================== LEAVE CANCELLATION ====================

class LeaveCancellationAPIView(APIView):
    """Leave Cancellation"""
    permission_classes = [IsAuthenticated]
    
    @transaction.atomic
    def post(self, request, application_id):
        """Cancel leave application"""
        try:
            application = get_object_or_404(LeaveApplication, id=application_id)
            cancellation_reason = request.data.get('reason', '')
            
            if application.status == 'cancelled':
                return Response({
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Leave is already cancelled"
                }, status=status.HTTP_400_BAD_REQUEST)
            
            calculator = LeaveCalculator(application.user, application.leave_type, application.from_date.year)
            balance = calculator.get_leave_balance()
            
            # Revert balance based on status
            if application.status == 'approved':
                balance.used -= application.total_days
            elif application.status == 'pending':
                balance.pending -= application.total_days
            
            balance.cancelled += application.total_days
            balance.save()
            
            application.status = 'cancelled'
            application.cancelled_at = timezone.now()
            application.cancelled_by = request.user
            application.cancellation_reason = cancellation_reason
            application.save()
            
            return Response({
                "status": status.HTTP_200_OK,
                "message": "Leave cancelled successfully",
                "data": LeaveApplicationSerializer(application).data
            })
            
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==================== COMPENSATORY OFF ====================

class CompensatoryOffAPIView(APIView):
    """Compensatory Off Management"""
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination
    
    def get(self, request, admin_id, user_id=None, pk=None):
        """Get comp offs"""
        try:
            admin = get_object_or_404(BaseUserModel, id=admin_id, role='admin')
            
            if pk:
                comp_off = get_object_or_404(CompensatoryOff, id=pk, admin=admin)
                serializer = CompensatoryOffSerializer(comp_off)
                return Response({
                    "status": status.HTTP_200_OK,
                    "message": "Comp off fetched successfully",
                    "data": serializer.data
                })
            else:
                queryset = CompensatoryOff.objects.filter(admin=admin)
                if user_id:
                    user = get_object_or_404(BaseUserModel, id=user_id, role='user')
                    queryset = queryset.filter(user=user)
                
                paginator = self.pagination_class()
                paginated_qs = paginator.paginate_queryset(queryset, request)
                serializer = CompensatoryOffSerializer(paginated_qs, many=True)
                pagination_data = paginator.get_paginated_response(serializer.data)
                pagination_data["results"] = serializer.data
                pagination_data["message"] = "Comp offs fetched successfully"
                
                return Response(pagination_data)
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def post(self, request, admin_id, user_id=None):
        """Create comp off"""
        try:
            admin = get_object_or_404(BaseUserModel, id=admin_id, role='admin')
            employee_id = user_id or request.data.get('user_id')
            user = get_object_or_404(BaseUserModel, id=employee_id, role='user')
            
            data = request.data.copy()
            data['admin'] = str(admin.id)
            data['user'] = str(user.id)
            
            # Calculate comp off days
            work_start = datetime.strptime(data.get('work_start_time'), '%H:%M:%S').time()
            work_end = datetime.strptime(data.get('work_end_time'), '%H:%M:%S').time()
            
            start_dt = datetime.combine(date.today(), work_start)
            end_dt = datetime.combine(date.today(), work_end)
            if end_dt < start_dt:
                end_dt += timedelta(days=1)
            
            total_hours = (end_dt - start_dt).total_seconds() / 3600
            comp_off_days = Decimal(str(total_hours / 8))  # Assuming 8 hours = 1 day
            
            data['total_hours'] = float(total_hours)
            data['comp_off_days'] = float(comp_off_days)
            
            serializer = CompensatoryOffSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                return Response({
                    "status": status.HTTP_201_CREATED,
                    "message": "Comp off created successfully",
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
    
    def put(self, request, admin_id, pk):
        """Approve/Reject comp off"""
        try:
            comp_off = get_object_or_404(CompensatoryOff, id=pk, admin_id=admin_id)
            action = request.data.get('action')
            
            if action == 'approve':
                comp_off.status = 'approved'
                comp_off.approved_by = request.user
                comp_off.approved_at = timezone.now()
                comp_off.comments = request.data.get('comments', '')
                comp_off.save()
                
                return Response({
                    "status": status.HTTP_200_OK,
                    "message": "Comp off approved successfully",
                    "data": CompensatoryOffSerializer(comp_off).data
                })
            elif action == 'reject':
                comp_off.status = 'rejected'
                comp_off.approved_by = request.user
                comp_off.approved_at = timezone.now()
                comp_off.comments = request.data.get('comments', '')
                comp_off.save()
                
                return Response({
                    "status": status.HTTP_200_OK,
                    "message": "Comp off rejected",
                    "data": CompensatoryOffSerializer(comp_off).data
                })
            else:
                return Response({
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Invalid action"
                }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==================== LEAVE ENCASHMENT ====================

class LeaveEncashmentAPIView(APIView):
    """Leave Encashment Management"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, admin_id, user_id=None, pk=None):
        """Get encashments"""
        try:
            admin = get_object_or_404(BaseUserModel, id=admin_id, role='admin')
            
            if pk:
                encashment = get_object_or_404(LeaveEncashment, id=pk, admin=admin)
                serializer = LeaveEncashmentSerializer(encashment)
                return Response({
                    "status": status.HTTP_200_OK,
                    "message": "Encashment fetched successfully",
                    "data": serializer.data
                })
            else:
                queryset = LeaveEncashment.objects.filter(admin=admin)
                if user_id:
                    user = get_object_or_404(BaseUserModel, id=user_id, role='user')
                    queryset = queryset.filter(user=user)
                
                serializer = LeaveEncashmentSerializer(queryset, many=True)
                return Response({
                    "status": status.HTTP_200_OK,
                    "message": "Encashments fetched successfully",
                    "data": serializer.data
                })
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @transaction.atomic
    def post(self, request, admin_id):
        """Create leave encashment"""
        try:
            admin = get_object_or_404(BaseUserModel, id=admin_id, role='admin')
            user_id = request.data.get('user_id')
            leave_type_id = request.data.get('leave_type_id')
            days_to_encash = Decimal(str(request.data.get('days_to_encash', 0)))
            daily_rate = Decimal(str(request.data.get('daily_rate', 0)))
            
            user = get_object_or_404(BaseUserModel, id=user_id, role='user')
            leave_type = get_object_or_404(LeaveType, id=leave_type_id)
            
            calculator = LeaveCalculator(user, leave_type)
            encashment_data = calculator.calculate_leave_encashment(days_to_encash, daily_rate)
            
            if not encashment_data:
                return Response({
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Encashment not allowed or insufficient balance"
                }, status=status.HTTP_400_BAD_REQUEST)
            
            balance = calculator.get_leave_balance()
            
            encashment = LeaveEncashment.objects.create(
                admin=admin,
                user=user,
                leave_type=leave_type,
                leave_balance=balance,
                encashment_date=date.today(),
                days_to_encash=encashment_data['days_to_encash'],
                encashment_percentage=encashment_data['encashment_percentage'],
                daily_rate=daily_rate,
                encashment_amount=encashment_data['encashment_amount'],
                reason=request.data.get('reason', ''),
                status='pending'
            )
            
            serializer = LeaveEncashmentSerializer(encashment)
            return Response({
                "status": status.HTTP_201_CREATED,
                "message": "Encashment request created successfully",
                "data": serializer.data
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @transaction.atomic
    def put(self, request, admin_id, pk):
        """Approve/Process encashment"""
        try:
            encashment = get_object_or_404(LeaveEncashment, id=pk, admin_id=admin_id)
            action = request.data.get('action')
            
            if action == 'approve':
                encashment.status = 'approved'
                encashment.approved_by = request.user
                encashment.approved_at = timezone.now()
                encashment.comments = request.data.get('comments', '')
                encashment.save()
                
                # Update balance
                balance = encashment.leave_balance
                balance.encashed += encashment.days_to_encash
                balance.used += encashment.days_to_encash
                balance.save()
                
                return Response({
                    "status": status.HTTP_200_OK,
                    "message": "Encashment approved successfully",
                    "data": LeaveEncashmentSerializer(encashment).data
                })
            elif action == 'process':
                encashment.status = 'processed'
                encashment.processed_at = timezone.now()
                encashment.payroll_month = request.data.get('payroll_month')
                encashment.payroll_year = request.data.get('payroll_year')
                encashment.save()
                
                return Response({
                    "status": status.HTTP_200_OK,
                    "message": "Encashment processed successfully",
                    "data": LeaveEncashmentSerializer(encashment).data
                })
            else:
                return Response({
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Invalid action"
                }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==================== LEAVE BALANCE ADJUSTMENT ====================

class LeaveBalanceAdjustmentAPIView(APIView):
    """Leave Balance Adjustment"""
    permission_classes = [IsAuthenticated]
    
    @transaction.atomic
    def post(self, request, admin_id):
        """Create balance adjustment"""
        try:
            admin = get_object_or_404(BaseUserModel, id=admin_id, role='admin')
            user_id = request.data.get('user_id')
            leave_type_id = request.data.get('leave_type_id')
            adjustment_type = request.data.get('adjustment_type')
            days = Decimal(str(request.data.get('days', 0)))
            
            user = get_object_or_404(BaseUserModel, id=user_id, role='user')
            leave_type = get_object_or_404(LeaveType, id=leave_type_id)
            
            calculator = LeaveCalculator(user, leave_type)
            balance = calculator.get_leave_balance()
            
            balance_before = balance.assigned
            
            if adjustment_type == 'credit':
                balance.assigned += days
            elif adjustment_type == 'debit':
                balance.assigned -= days
            elif adjustment_type == 'correction':
                balance.assigned = days
            
            balance.save()
            
            adjustment = LeaveBalanceAdjustment.objects.create(
                admin=admin,
                user=user,
                leave_type=leave_type,
                leave_balance=balance,
                adjustment_date=date.today(),
                adjustment_type=adjustment_type,
                days=days,
                balance_before=balance_before,
                balance_after=balance.assigned,
                reason=request.data.get('reason', ''),
                approved_by=request.user,
                created_by=request.user
            )
            
            serializer = LeaveBalanceAdjustmentSerializer(adjustment)
            return Response({
                "status": status.HTTP_201_CREATED,
                "message": "Balance adjustment created successfully",
                "data": serializer.data
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==================== LEAVE ACCRUAL PROCESSING ====================

class LeaveAccrualProcessAPIView(APIView):
    """Process Leave Accruals"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request, admin_id):
        """Process accruals for employees"""
        try:
            admin = get_object_or_404(BaseUserModel, id=admin_id, role='admin')
            user_ids = request.data.get('user_ids', [])  # Optional: specific users
            leave_type_ids = request.data.get('leave_type_ids', [])  # Optional: specific leave types
            accrual_date = request.data.get('accrual_date', date.today().isoformat())
            accrual_date = datetime.strptime(accrual_date, '%Y-%m-%d').date()
            
            # Get employees
            if user_ids:
                users = BaseUserModel.objects.filter(id__in=user_ids, role='user')
            else:
                user_profiles = UserProfile.objects.filter(admin=admin)
                users = [profile.user for profile in user_profiles]
            
            # Get leave types
            if leave_type_ids:
                leave_types = LeaveType.objects.filter(id__in=leave_type_ids, accrual_enabled=True)
            else:
                leave_types = LeaveType.objects.filter(organization=admin.own_admin_profile.organization, accrual_enabled=True)
            
            processed = []
            errors = []
            
            for user in users:
                for leave_type in leave_types:
                    try:
                        calculator = LeaveCalculator(user, leave_type, accrual_date.year)
                        accrual_log = calculator.process_leave_accrual(accrual_date)
                        if accrual_log:
                            processed.append({
                                'user_id': str(user.id),
                                'leave_type': leave_type.code,
                                'days_accrued': float(accrual_log.days_accrued)
                            })
                    except Exception as e:
                        errors.append(f"Error for {user.email} - {leave_type.code}: {str(e)}")
            
            return Response({
                "status": status.HTTP_200_OK,
                "message": f"Processed {len(processed)} accruals",
                "processed": processed,
                "errors": errors if errors else None
            })
            
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==================== LEAVE CALENDAR ====================

class LeaveCalendarAPIView(APIView):
    """Leave Calendar View"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, admin_id, month=None, year=None):
        """Get leave calendar"""
        try:
            admin = get_object_or_404(BaseUserModel, id=admin_id, role='admin')
            
            if not month or not year:
                today = date.today()
                month = today.month
                year = today.year
            
            # Get all leave applications for the month
            start_date = date(year, month, 1)
            if month == 12:
                end_date = date(year + 1, 1, 1) - timedelta(days=1)
            else:
                end_date = date(year, month + 1, 1) - timedelta(days=1)
            
            leaves = LeaveApplication.objects.filter(
                admin=admin,
                from_date__lte=end_date,
                to_date__gte=start_date,
                status__in=['approved', 'pending']
            ).select_related('user', 'leave_type')
            
            calendar_events = []
            for leave in leaves:
                current_date = max(leave.from_date, start_date)
                end_leave_date = min(leave.to_date, end_date)
                
                while current_date <= end_leave_date:
                    calendar_events.append({
                        'date': current_date.isoformat(),
                        'user_id': str(leave.user.id),
                        'user_name': leave.user.own_user_profile.user_name,
                        'leave_type': leave.leave_type.code,
                        'leave_type_name': leave.leave_type.name,
                        'color': leave.leave_type.color_code,
                        'status': leave.status,
                        'is_full_day': leave.duration_type == 'full_day'
                    })
                    current_date += timedelta(days=1)
            
            return Response({
                "status": status.HTTP_200_OK,
                "message": "Calendar fetched successfully",
                "data": calendar_events,
                "month": month,
                "year": year
            })
            
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==================== LEAVE REPORTS ====================

class LeaveReportAPIView(APIView):
    """Leave Reports and Analytics"""
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination
    
    def get(self, request, admin_id):
        """Get leave reports"""
        try:
            admin = get_object_or_404(BaseUserModel, id=admin_id, role='admin')
            report_type = request.query_params.get('type', 'summary')
            year = int(request.query_params.get('year', date.today().year))
            month = request.query_params.get('month')
            
            if report_type == 'summary':
                # Summary report
                user_profiles = UserProfile.objects.filter(admin=admin)
                employee_ids = [profile.user.id for profile in user_profiles]
                
                balances = EmployeeLeaveBalance.objects.filter(
                    user_id__in=employee_ids,
                    year=year,
                    is_active=True
                ).select_related('user', 'leave_type')
                
                summary = {}
                for balance in balances:
                    user_id = str(balance.user.id)
                    if user_id not in summary:
                        summary[user_id] = {
                            'user_id': user_id,
                            'user_name': balance.user.own_user_profile.user_name,
                            'email': balance.user.email,
                            'leave_types': {}
                        }
                    
                    summary[user_id]['leave_types'][balance.leave_type.code] = {
                        'assigned': float(balance.assigned),
                        'used': float(balance.used),
                        'pending': float(balance.pending),
                        'balance': float(balance.balance),
                        'encashed': float(balance.encashed)
                    }
                
                return Response({
                    "status": status.HTTP_200_OK,
                    "message": "Summary report fetched successfully",
                    "data": list(summary.values()),
                    "year": year
                })
            
            elif report_type == 'utilization':
                # Utilization report
                leaves = LeaveApplication.objects.filter(
                    admin=admin,
                    from_date__year=year,
                    status='approved'
                )
                
                if month:
                    leaves = leaves.filter(from_date__month=month)
                
                utilization = leaves.values('leave_type__code', 'leave_type__name').annotate(
                    total_applications=Count('id'),
                    total_days=Sum('total_days'),
                    avg_days=Avg('total_days')
                )
                
                return Response({
                    "status": status.HTTP_200_OK,
                    "message": "Utilization report fetched successfully",
                    "data": list(utilization),
                    "year": year,
                    "month": month
                })
            
            else:
                return Response({
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Invalid report type"
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==================== LEAVE EXCEL EXPORT ====================

class LeaveExcelExportAPIView(APIView):
    """Leave Excel Export"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, admin_id):
        """Export leave data to Excel"""
        try:
            admin = get_object_or_404(BaseUserModel, id=admin_id, role='admin')
            export_type = request.query_params.get('type', 'balance')  # 'balance' or 'applications'
            year = int(request.query_params.get('year', date.today().year))
            month = request.query_params.get('month')
            
            user_profiles = UserProfile.objects.filter(admin=admin)
            employee_ids = [profile.user.id for profile in user_profiles]
            
            if export_type == 'balance':
                # Export leave balances
                balances = EmployeeLeaveBalance.objects.filter(
                    user_id__in=employee_ids,
                    year=year,
                    is_active=True
                ).select_related('user', 'leave_type')
                
                return LeaveExcelService.generate_leave_balance_excel(balances, year)
            
            elif export_type == 'applications':
                # Export leave applications
                applications = LeaveApplication.objects.filter(
                    admin=admin,
                    from_date__year=year
                )
                
                if month:
                    applications = applications.filter(from_date__month=int(month))
                
                return LeaveExcelService.generate_leave_application_excel(applications, month, year)
            
            else:
                return Response({
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Invalid export type. Use 'balance' or 'applications'"
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==================== LEAVE SUMMARY DASHBOARD ====================

class LeaveSummaryDashboardAPIView(APIView):
    """Leave Summary Dashboard"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, admin_id):
        """Get leave summary dashboard"""
        try:
            admin = get_object_or_404(BaseUserModel, id=admin_id, role='admin')
            year = int(request.query_params.get('year', date.today().year))
            
            user_profiles = UserProfile.objects.filter(admin=admin)
            employee_ids = [profile.user.id for profile in user_profiles]
            
            # Total employees
            total_employees = len(employee_ids)
            
            # Leave balances summary
            balances = EmployeeLeaveBalance.objects.filter(
                user_id__in=employee_ids,
                year=year,
                is_active=True
            )
            
            # Leave applications summary
            applications = LeaveApplication.objects.filter(
                admin=admin,
                from_date__year=year
            )
            
            # Statistics
            total_applications = applications.count()
            pending_applications = applications.filter(status='pending').count()
            approved_applications = applications.filter(status='approved').count()
            rejected_applications = applications.filter(status='rejected').count()
            
            # Leave utilization by type
            utilization_by_type = applications.filter(status='approved').values(
                'leave_type__code', 'leave_type__name'
            ).annotate(
                total_days=Sum('total_days'),
                count=Count('id')
            )
            
            # Top leave takers
            top_leave_takers = applications.filter(status='approved').values(
                'user__id', 'user__own_user_profile__user_name'
            ).annotate(
                total_days=Sum('total_days')
            ).order_by('-total_days')[:10]
            
            # Leave balance summary
            balance_summary = balances.values('leave_type__code', 'leave_type__name').aggregate(
                total_assigned=Sum('assigned'),
                total_used=Sum('used'),
                total_pending=Sum('pending'),
                total_balance=Sum('assigned') - Sum('used') - Sum('pending')
            )
            
            return Response({
                "status": status.HTTP_200_OK,
                "message": "Dashboard data fetched successfully",
                "data": {
                    "year": year,
                    "total_employees": total_employees,
                    "applications": {
                        "total": total_applications,
                        "pending": pending_applications,
                        "approved": approved_applications,
                        "rejected": rejected_applications
                    },
                    "utilization_by_type": list(utilization_by_type),
                    "top_leave_takers": list(top_leave_takers),
                    "balance_summary": balance_summary
                }
            })
            
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

