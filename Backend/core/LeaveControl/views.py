from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from datetime import datetime
from .models import LeaveType, EmployeeLeaveBalance, LeaveApplication
from .serializers import (
    LeaveTypeSerializer, LeaveTypeUpdateSerializer,
    EmployeeLeaveBalanceSerializer, EmployeeLeaveBalanceUpdateSerializer,
    LeaveApplicationSerializer, LeaveApplicationUpdateSerializer
)
from AuthN.models import AdminProfile, UserProfile


class LeaveTypeAPIView(APIView):
    """Leave Type CRUD operations"""
    
    def get(self, request, admin_id, pk=None):
        if pk:
            leave = get_object_or_404(LeaveType, admin__id=admin_id, id=pk, is_active=True)
            serializer = LeaveTypeSerializer(leave)
            return Response({
                "status": status.HTTP_200_OK,
                "message": "Leave type fetched successfully",
                "data": serializer.data
            })
        leaves = LeaveType.objects.filter(admin__id=admin_id, is_active=True)
        serializer = LeaveTypeSerializer(leaves, many=True)
        return Response({
            "status": status.HTTP_200_OK,
            "message": "Leave types fetched successfully",
            "data": serializer.data
        })

    def post(self, request, admin_id, pk=None):
        admin = get_object_or_404(AdminProfile, user_id=admin_id)
        data = request.data.copy()
        data['admin'] = admin.user_id

        serializer = LeaveTypeSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "status": status.HTTP_201_CREATED,
                "message": "Leave type created successfully",
                "data": serializer.data
            }, status=status.HTTP_201_CREATED)
        return Response({
            "status": status.HTTP_400_BAD_REQUEST,
            "message": "Validation failed",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, admin_id, pk):
        leave = get_object_or_404(LeaveType, admin__id=admin_id, id=pk)
        serializer = LeaveTypeUpdateSerializer(leave, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "status": status.HTTP_200_OK,
                "message": "Leave type updated successfully",
                "data": serializer.data
            })
        return Response({
            "status": status.HTTP_400_BAD_REQUEST,
            "message": "Validation failed",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, admin_id, pk):
        leave = get_object_or_404(LeaveType, admin__id=admin_id, id=pk)
        serializer = LeaveTypeSerializer(leave, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "status": status.HTTP_200_OK,
                "message": "Leave type updated successfully",
                "data": serializer.data
            })
        return Response({
            "status": status.HTTP_400_BAD_REQUEST,
            "message": "Validation failed",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, admin_id, pk):
        leave = get_object_or_404(LeaveType, admin__id=admin_id, id=pk)
        
        # Check if leave type is assigned to any employee
        # Get unique employee count (not total records)
        assigned_employees = EmployeeLeaveBalance.objects.filter(
            leave_type=leave
        ).values_list('user', flat=True).distinct()
        
        assigned_count = assigned_employees.count()
        
        if assigned_count > 0:
            return Response({
                "status": status.HTTP_400_BAD_REQUEST,
                "message": f"Cannot delete '{leave.name}'. This leave type is currently assigned to {assigned_count} employee(s). Please unassign this leave type from all employees before deleting.",
                "data": {
                    "assigned_employees_count": assigned_count,
                    "total_assignments": EmployeeLeaveBalance.objects.filter(
                        leave_type=leave
                    ).count(),
                    "leave_type_name": leave.name
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if leave type has any applications
        applications_count = LeaveApplication.objects.filter(
            leave_type=leave
        ).count()
        
        if applications_count > 0:
            return Response({
                "status": status.HTTP_400_BAD_REQUEST,
                "message": f"Cannot delete '{leave.name}'. This leave type has {applications_count} leave application(s) associated with it. Deleting it would result in loss of historical data.",
                "data": {
                    "applications_count": applications_count,
                    "leave_type_name": leave.name
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Safe to delete
        leave.is_active = False
        leave.save()
        return Response({
            "status": status.HTTP_200_OK,
            "message": f"{leave.name} deleted successfully",
            "data": None
        })


class EmployeeLeaveBalanceAPIView(APIView):
    """
    Employee Leave Balance - View & Update Only
    Supports both admin_id (all employees) and user_id (specific user)
    Note: For assigning leaves, use AssignLeaveAPIView
    """
    
    def get(self, request, admin_id=None, user_id=None, pk=None):
        """
        GET /leave-balances/<admin_id>?year=2025 -> All employees under admin (year optional)
        GET /leave-balances/<admin_id>/<user_id>?year=2025 -> Specific employee (year optional)
        GET /leave-balances/<admin_id>/<user_id>/<pk> -> Specific balance
        """
        # Get year from query params (optional)
        year = request.GET.get('year')
        
        # Specific balance by ID
        if pk:
            if user_id:
                balance = get_object_or_404(EmployeeLeaveBalance, user__id=user_id, id=pk)
            else:
                balance = get_object_or_404(EmployeeLeaveBalance, id=pk)
            serializer = EmployeeLeaveBalanceSerializer(balance)
            return Response({
                "status": status.HTTP_200_OK,
                "message": "Leave balance fetched successfully",
                "data": serializer.data
            })
        
        # Admin viewing all employees' balances
        if admin_id and not user_id:
            # Get all users under this admin
            from AuthN.models import UserProfile
            admin_users = UserProfile.objects.filter(admin_id=admin_id).values_list('user_id', flat=True)
            
            # Build query with optional year filter
            query = {
                'user__id__in': admin_users
            }
            if year:
                query['year'] = int(year)
            
            balances = EmployeeLeaveBalance.objects.filter(
                **query
            ).select_related('user', 'leave_type').order_by('-year', 'user__email', 'leave_type__name')
            
            serializer = EmployeeLeaveBalanceSerializer(balances, many=True)
            
            message = f"All employees leave balances fetched successfully"
            if year:
                message += f" for year {year}"
            
            return Response({
                "status": status.HTTP_200_OK,
                "message": message,
                "data": serializer.data
            })
        
        # Specific user's balances
        if user_id:
            # Build query with optional year filter
            query = {
                'user__id': user_id
            }
            if year:
                query['year'] = int(year)
            
            balances = EmployeeLeaveBalance.objects.filter(**query).order_by('-year', 'leave_type__name')
            serializer = EmployeeLeaveBalanceSerializer(balances, many=True)
            
            message = f"Leave balances fetched successfully"
            if year:
                message += f" for year {year}"
            
            return Response({
                "status": status.HTTP_200_OK,
                "message": message,
                "data": serializer.data
            })
        
        return Response({
            "status": status.HTTP_400_BAD_REQUEST,
            "message": "Invalid request",
            "data": None
        }, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, admin_id=None, user_id=None, pk=None):
        """
        Update leave balance - Only 'assigned' field can be updated
        Cannot change user, leave_type, year, used, etc.
        """
        leave_balance = get_object_or_404(EmployeeLeaveBalance, id=pk)
        
        # Only allow updating 'assigned' field
        if 'assigned' not in request.data:
            return Response({
                "status": status.HTTP_400_BAD_REQUEST,
                "message": "Only 'assigned' field can be updated",
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)
        
        assigned = float(request.data['assigned'])
        
        # Validation: assigned cannot exceed default_count
        leave_type = leave_balance.leave_type
        if assigned > float(leave_type.default_count):
            return Response({
                "status": status.HTTP_400_BAD_REQUEST,
                "message": f"Cannot assign {assigned} days for {leave_type.name}. Maximum allowed is {leave_type.default_count} days",
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validation: assigned should be >= used (cannot reduce below used)
        from decimal import Decimal
        used_value = Decimal(str(leave_balance.used))
        assigned_decimal = Decimal(str(assigned))
        
        if assigned_decimal < used_value:
            return Response({
                "status": status.HTTP_400_BAD_REQUEST,
                "message": f"Cannot assign {assigned} days. Employee has already used {leave_balance.used} days",
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Update only assigned field
        leave_balance.assigned = assigned
        leave_balance.save()
        
        serializer = EmployeeLeaveBalanceSerializer(leave_balance)
        return Response({
            "status": status.HTTP_200_OK,
            "message": "Leave balance updated successfully",
            "data": serializer.data
        })

    def delete(self, request, admin_id=None, user_id=None, pk=None):
        """Delete leave balance (unassign leave from employee)"""
        leave_balance = get_object_or_404(EmployeeLeaveBalance, id=pk)
        
        # Check if employee has used any leaves
        if leave_balance.used > 0:
            return Response({
                "status": status.HTTP_400_BAD_REQUEST,
                "message": f"Cannot unassign {leave_balance.leave_type.name}. Employee has already used {leave_balance.used} days.",
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Hard delete the record
        leave_type_name = leave_balance.leave_type.name
        leave_balance.delete()
        
        return Response({
            "status": status.HTTP_200_OK,
            "message": f"{leave_type_name} unassigned successfully",
            "data": None
        })


class AssignLeaveAPIView(APIView):
    """
    Flexible Leave Assignment API - Single aur Bulk dono handle karta hai
    Auto-assigns default_count if 'assigned' not provided
    
    Single Format (assigned optional):
    {
        "year": 2024,
        "leave_type": 1
    }
    OR
    {
        "year": 2024,
        "leave_type": 1,
        "assigned": 12
    }
    
    Bulk Format (assigned optional):
    {
        "year": 2024,
        "leaves": [
            {"leave_type": 1},
            {"leave_type": 2, "assigned": 10}
        ]
    }
    """
    
    def post(self, request, admin_id=None, user_id=None):
        """Assign leave(s) to a user - single ya bulk"""
        # Get user_id from URL or request body
        target_user_id = user_id or request.data.get('user_id')
        if not target_user_id:
            return Response({
                "status": status.HTTP_400_BAD_REQUEST,
                "message": "user_id is required",
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get user directly from BaseUserModel
        from AuthN.models import BaseUserModel
        try:
            user = BaseUserModel.objects.get(id=target_user_id, role='user')
        except BaseUserModel.DoesNotExist:
            return Response({
                "status": status.HTTP_400_BAD_REQUEST,
                "message": f"User with ID {target_user_id} not found or not a valid employee",
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)
        
        year = request.data.get('year')
        
        if not year:
            return Response({
                "status": status.HTTP_400_BAD_REQUEST,
                "message": "Year is required",
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if single or bulk format
        leaves_list = []
        
        # Single leave format check
        if 'leave_type' in request.data:
            leaves_list.append({
                'leave_type': request.data.get('leave_type'),
                'assigned': request.data.get('assigned')  # Can be None
            })
        # Bulk leaves format check
        elif 'leaves' in request.data:
            leaves_list = request.data.get('leaves', [])
        else:
            return Response({
                "status": status.HTTP_400_BAD_REQUEST,
                "message": "Either 'leave_type' or 'leaves' array is required",
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not leaves_list:
            return Response({
                "status": status.HTTP_400_BAD_REQUEST,
                "message": "At least one leave type is required",
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)
        
        created_balances = []
        errors = []
        
        for leave_data in leaves_list:
            leave_type_id = leave_data.get('leave_type')
            assigned = leave_data.get('assigned')  # Can be None
            
            if not leave_type_id:
                errors.append({
                    "error": "leave_type is required for each entry"
                })
                continue
            
            # Get leave type to fetch default_count if assigned not provided
            try:
                leave_type = LeaveType.objects.get(id=leave_type_id, is_active=True)
                
                # If assigned not provided, use default_count from leave type
                if assigned is None:
                    assigned = leave_type.default_count
                else:
                    assigned = float(assigned)
                    
                    # Validation: assigned should not exceed default_count
                    if assigned > float(leave_type.default_count):
                        errors.append({
                            "leave_type": leave_type_id,
                            "leave_type_name": leave_type.name,
                            "leave_type_code": leave_type.code,
                            "error": f"Cannot assign {assigned} days. Maximum allowed is {leave_type.default_count} days (default count)"
                        })
                        continue
                    
            except LeaveType.DoesNotExist:
                errors.append({
                    "leave_type": leave_type_id,
                    "error": "Leave type not found or inactive"
                })
                continue
            
            # Check if balance already exists
            existing_balance = EmployeeLeaveBalance.objects.filter(
                user__id=target_user_id,
                leave_type_id=leave_type_id,
                year=year
            ).first()
            
            if existing_balance:
                errors.append({
                    "leave_type": leave_type_id,
                    "leave_type_name": leave_type.name,
                    "error": f"Balance already exists for {leave_type.name} ({leave_type.code}) in {year}"
                })
                continue
            
            # Create new balance
            try:
                balance = EmployeeLeaveBalance.objects.create(
                    user=user,
                    leave_type_id=leave_type_id,
                    year=year,
                    assigned=assigned,
                    used=0
                )
                created_balances.append({
                    "id": balance.id,
                    "leave_type": leave_type_id,
                    "leave_type_name": leave_type.name,
                    "leave_type_code": leave_type.code,
                    "assigned": float(assigned),
                    "used": 0,
                    "balance": float(assigned)
                })
            except Exception as e:
                errors.append({
                    "leave_type": leave_type_id,
                    "leave_type_name": leave_type.name,
                    "error": str(e)
                })
        
        if created_balances:
            return Response({
                "status": status.HTTP_201_CREATED,
                "message": f"Successfully assigned {len(created_balances)} leave type(s)",
                "data": {
                    "created": created_balances,
                    "errors": errors
                }
            }, status=status.HTTP_201_CREATED)
        else:
            return Response({
                "status": status.HTTP_400_BAD_REQUEST,
                "message": "Failed to assign leaves",
                "data": {
                    "created": [],
                    "errors": errors
                }
            }, status=status.HTTP_400_BAD_REQUEST)


class LeaveApplicationAPIView(APIView):
    """
    Leave Application CRUD operations
    Supports both admin_id (all employees) and user_id (specific user)
    """
    
    def get_year_date_range(self, organization_id, year):
        """
        Calculate date range based on organization's leave year type
        Returns: (start_date, end_date) tuple
        """
        from AuthN.models import OrganizationSettings, BaseUserModel
        from datetime import date
        
        try:
            org = BaseUserModel.objects.get(id=organization_id, role='organization')
            org_settings = OrganizationSettings.objects.filter(organization=org).first()
            
            if not org_settings:
                # Default to calendar year if no settings
                return date(year, 1, 1), date(year, 12, 31)
            
            leave_year_type = org_settings.leave_year_type
            start_month = org_settings.leave_year_start_month or 1
            
            if leave_year_type == 'calendar':
                # Calendar Year: Jan 1 to Dec 31
                start_date = date(year, 1, 1)
                end_date = date(year, 12, 31)
            elif leave_year_type == 'financial':
                # Financial Year (India): Apr 1 to Mar 31 next year
                # If year is 2025, it means Apr 1, 2025 to Mar 31, 2026
                start_date = date(year, 4, 1)
                end_date = date(year + 1, 3, 31)
            elif leave_year_type == 'custom':
                # Custom year based on start_month
                start_date = date(year, start_month, 1)
                # End date is last day of month before start_month next year
                if start_month == 1:
                    end_date = date(year, 12, 31)
                else:
                    import calendar
                    end_month = start_month - 1
                    end_year = year + 1
                    last_day = calendar.monthrange(end_year, end_month)[1]
                    end_date = date(end_year, end_month, last_day)
            else:
                # Default to calendar
                start_date = date(year, 1, 1)
                end_date = date(year, 12, 31)
            
            return start_date, end_date
        except Exception as e:
            # Fallback to calendar year
            return date(year, 1, 1), date(year, 12, 31)

    def get(self, request, admin_id=None, user_id=None, pk=None):
        """
        GET /leave-applications/<admin_id>?year=2025 -> All employees' applications (year REQUIRED)
        GET /leave-applications/<admin_id>/<user_id>?year=2025 -> Specific employee's applications (year REQUIRED)
        GET /leave-applications/<admin_id>/<user_id>/<pk> -> Specific application (year not needed)
        
        Year filtering respects organization's leave year type (calendar/financial/custom)
        """
        # Specific leave application by ID (no year needed)
        if pk:
            if user_id:
                leave = get_object_or_404(LeaveApplication, user__id=user_id, id=pk)
            else:
                leave = get_object_or_404(LeaveApplication, id=pk)
            serializer = LeaveApplicationSerializer(leave)
            return Response({
                "status": status.HTTP_200_OK,
                "message": "Leave application fetched successfully",
                "data": serializer.data
            })
        
        # Year parameter is REQUIRED for listing
        year_param = request.GET.get('year')
        if not year_param:
            return Response({
                "status": status.HTTP_400_BAD_REQUEST,
                "message": "Year parameter is required. Please provide ?year=2025",
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate and parse year
        try:
            year = int(year_param)
            if year < 1900 or year > 2100:
                return Response({
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Invalid year. Year must be between 1900 and 2100",
                    "data": None
                }, status=status.HTTP_400_BAD_REQUEST)
        except ValueError:
            return Response({
                "status": status.HTTP_400_BAD_REQUEST,
                "message": "Invalid year format. Year must be a valid integer (e.g., 2025)",
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get organization_id from admin or user
        from AuthN.models import UserProfile
        if admin_id:
            admin_profile = UserProfile.objects.filter(user_id=admin_id).first()
            if admin_profile:
                org_id = admin_profile.organization_id
            else:
                org_id = None
        elif user_id:
            user_profile = UserProfile.objects.filter(user_id=user_id).first()
            if user_profile:
                org_id = user_profile.organization_id
            else:
                org_id = None
        else:
            org_id = None
        
        # Calculate date range based on organization's leave year type
        if org_id:
            start_date, end_date = self.get_year_date_range(org_id, year)
            date_filter = {
                'from_date__gte': start_date,
                'from_date__lte': end_date
            }
        else:
            # Fallback to calendar year if no org settings
            from datetime import date
            start_date = date(year, 1, 1)
            end_date = date(year, 12, 31)
            date_filter = {
                'from_date__gte': start_date,
                'from_date__lte': end_date
            }
        
        # Admin viewing all employees' applications
        if admin_id and not user_id:
            from AuthN.models import UserProfile
            admin_users = UserProfile.objects.filter(admin_id=admin_id).values_list('user_id', flat=True)
            leaves = LeaveApplication.objects.filter(
                user__id__in=admin_users,
                **date_filter
            ).select_related('user', 'leave_type', 'reviewed_by').order_by('-applied_at')
            
            serializer = LeaveApplicationSerializer(leaves, many=True)
            
            return Response({
                "status": status.HTTP_200_OK,
                "message": f"All employees leave applications for year {year}",
                "count": leaves.count(),
                "year": year,
                "date_range": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                },
                "data": serializer.data
            })
        
        # Specific user's applications
        if user_id:
            leaves = LeaveApplication.objects.filter(
                user__id=user_id,
                **date_filter
            ).order_by('-applied_at')
            
            serializer = LeaveApplicationSerializer(leaves, many=True)
            
            return Response({
                "status": status.HTTP_200_OK,
                "message": f"Leave applications fetched successfully for year {year}",
                "count": leaves.count(),
                "year": year,
                "date_range": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                },
                "data": serializer.data
            })
        
        return Response({
            "status": status.HTTP_400_BAD_REQUEST,
            "message": "Invalid request",
            "data": None
        }, status=status.HTTP_400_BAD_REQUEST)

    def post(self, request, admin_id=None, user_id=None, pk=None):
        """Create leave application"""
        # Get user_id from URL or request body
        target_user_id = user_id or request.data.get('user_id')
        if not target_user_id:
            return Response({
                "status": status.HTTP_400_BAD_REQUEST,
                "message": "user_id is required",
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get user from BaseUserModel
        from AuthN.models import BaseUserModel
        base_user = get_object_or_404(BaseUserModel, id=target_user_id, role='user')
        
        # Try to get UserProfile for admin_id and organization_id
        try:
            user_profile = UserProfile.objects.get(user=base_user)
            admin_id_val = user_profile.admin_id
            org_id_val = user_profile.organization_id
        except UserProfile.DoesNotExist:
            return Response({
                "status": status.HTTP_400_BAD_REQUEST,
                "message": "User profile not found. Please complete user setup.",
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)
        
        data = request.data.copy()
        data['user'] = target_user_id
        data['admin'] = admin_id_val
        data['organization'] = org_id_val

        from_date = data.get('from_date')
        to_date = data.get('to_date')

        if from_date and to_date:
            from_date_obj = datetime.strptime(from_date, '%Y-%m-%d').date()
            to_date_obj = datetime.strptime(to_date, '%Y-%m-%d').date()
            total_days = (to_date_obj - from_date_obj).days + 1
            data['total_days'] = total_days

            # Check for overlapping leave applications
            overlapping_leaves = LeaveApplication.objects.filter(
                user__id=target_user_id,
                from_date__lte=to_date_obj,
                to_date__gte=from_date_obj
            ).exclude(status='cancelled')
            
            if overlapping_leaves.exists():
                existing = overlapping_leaves.first()
                return Response({
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": f"Leave already applied for overlapping dates ({existing.from_date} to {existing.to_date}). Please choose different dates.",
                    "data": {
                        "existing_leave": {
                            "from_date": existing.from_date,
                            "to_date": existing.to_date,
                            "status": existing.status,
                            "leave_type": existing.leave_type.name
                        }
                    }
                }, status=status.HTTP_400_BAD_REQUEST)

            # Validate and fetch leave balance
            balance = EmployeeLeaveBalance.objects.filter(
                user__id=target_user_id,
                leave_type_id=data['leave_type'],
                year=from_date_obj.year
            ).first()

            if not balance:
                return Response({
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Leave balance not found for this year",
                    "data": None
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if balance.balance < total_days:
                return Response({
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": f"Insufficient leave balance. Available: {balance.balance}, Required: {total_days}",
                    "data": None
                }, status=status.HTTP_400_BAD_REQUEST)

        serializer = LeaveApplicationSerializer(data=data)
        if serializer.is_valid():
            leave_app = serializer.save()

            # Sync balance based on all pending + approved leaves
            if from_date and to_date:
                from .balance_sync import sync_leave_balance
                sync_leave_balance(
                    user_id=target_user_id,
                    leave_type_id=leave_app.leave_type.id,
                    year=from_date_obj.year
                )

            return Response({
                "status": status.HTTP_201_CREATED,
                "message": "Leave application created successfully",
                "data": serializer.data
            }, status=status.HTTP_201_CREATED)
        
        return Response({
            "status": status.HTTP_400_BAD_REQUEST,
            "message": "Validation failed",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, admin_id=None, user_id=None, pk=None):
        """Update leave application - Handle status changes and balance updates"""
        leave = get_object_or_404(LeaveApplication, id=pk)
        old_status = leave.status
        new_status = request.data.get('status')
        
        print(f"🔄 PUT Leave: ID={pk}, Old Status={old_status}, New Status={new_status}")
        
        serializer = LeaveApplicationUpdateSerializer(leave, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            
            # Sync balance based on all pending + approved leaves
            if new_status and old_status != new_status:
                print(f"📊 Status changed from {old_status} to {new_status}")
                from .balance_sync import sync_leave_balance
                sync_leave_balance(
                    user_id=leave.user.id,
                    leave_type_id=leave.leave_type.id,
                    year=leave.from_date.year
                )
            
            return Response({
                "status": status.HTTP_200_OK,
                "message": f"Leave application {new_status or 'updated'} successfully",
                "data": serializer.data
            })
        return Response({
            "status": status.HTTP_400_BAD_REQUEST,
            "message": "Validation failed",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, admin_id=None, user_id=None, pk=None):
        """Cancel leave application - Only pending leaves can be cancelled"""
        leave = get_object_or_404(LeaveApplication, id=pk)
        
        # Only pending leaves can be cancelled
        if leave.status != 'pending':
            return Response({
                "status": status.HTTP_400_BAD_REQUEST,
                "message": f"Cannot cancel {leave.status} leave. Only pending leaves can be cancelled.",
                "data": {
                    "current_status": leave.status,
                    "from_date": leave.from_date,
                    "to_date": leave.to_date
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Store info before cancelling
        user_id = leave.user.id
        leave_type_id = leave.leave_type.id
        year = leave.from_date.year
        total_days = leave.total_days
        
        # Mark as cancelled
        leave.status = 'cancelled'
        leave.save()
        
        # Sync balance based on all pending + approved leaves
        from .balance_sync import sync_leave_balance
        sync_leave_balance(user_id, leave_type_id, year)
        
        return Response({
            "status": status.HTTP_200_OK,
            "message": "Leave application cancelled successfully. Balance restored.",
            "data": {
                "cancelled_leave": {
                    "id": leave.id,
                    "from_date": leave.from_date,
                    "to_date": leave.to_date,
                    "total_days": total_days,
                    "status": leave.status
                },
                "restored_balance": float(total_days)
            }
        })
