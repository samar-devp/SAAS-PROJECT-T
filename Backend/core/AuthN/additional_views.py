"""
Additional Utility APIs for AuthN Module
Comprehensive APIs for frontend usage
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.db.models import Q, Count, Sum, Avg
from django.utils import timezone
from datetime import datetime, date
from django.http import HttpResponse
import csv

from .models import (
    BaseUserModel, UserProfile, AdminProfile, OrganizationProfile,
    SystemOwnerProfile, OrganizationSettings
)
from .serializers import (
    UserProfileSerializer, AdminProfileSerializer, OrganizationProfileSerializer,
    SystemOwnerProfileSerializer, OrganizationSettingsSerializer
)
from utils.pagination_utils import CustomPagination


# ==================== CHANGE PASSWORD FOR ALL ROLES ====================

class ChangePasswordAllRolesAPIView(APIView):
    """Change password for any role (System Owner, Organization, Admin, User)"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request, user_id):
        try:
            user = get_object_or_404(BaseUserModel, id=user_id)
            current_user = request.user
            
            # Check if user is changing their own password or is admin/system_owner
            if user.id != current_user.id and current_user.role not in ['system_owner', 'organization', 'admin']:
                return Response({
                    "status": status.HTTP_403_FORBIDDEN,
                    "message": "You don't have permission to change this user's password"
                }, status=status.HTTP_403_FORBIDDEN)
            
            old_password = request.data.get("old_password")
            new_password = request.data.get("new_password")
            force_change = request.data.get("force_change", False)  # For admin/system_owner
            
            if not new_password:
                return Response({
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "New password is required"
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Check old password only if not force change
            if not force_change and old_password:
                if not user.check_password(old_password):
                    return Response({
                        "status": status.HTTP_400_BAD_REQUEST,
                        "message": "Old password is incorrect"
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            user.set_password(new_password)
            user.save()
            
            return Response({
                "status": status.HTTP_200_OK,
                "message": f"Password changed successfully for {user.email}"
            })
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==================== EMPLOYEE LIST UNDER ADMIN ====================

class EmployeeListUnderAdminAPIView(APIView):
    """Get all employees under an admin"""
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination
    
    def get(self, request, admin_id):
        try:
            admin = get_object_or_404(BaseUserModel, id=admin_id, role='admin')
            
            search = request.query_params.get("q", "")
            status_filter = request.query_params.get("status")  # active, inactive, all
            designation = request.query_params.get("designation")
            department = request.query_params.get("department")
            
            queryset = UserProfile.objects.filter(admin=admin)
            
            # Search
            if search:
                queryset = queryset.filter(
                    Q(user_name__icontains=search) |
                    Q(custom_employee_id__icontains=search) |
                    Q(designation__icontains=search) |
                    Q(user__email__icontains=search)
                )
            
            # Status filter
            if status_filter == 'active':
                queryset = queryset.filter(user__is_active=True)
            elif status_filter == 'inactive':
                queryset = queryset.filter(user__is_active=False)
            
            # Designation filter
            if designation:
                queryset = queryset.filter(designation__icontains=designation)
            
            # Department filter (if exists in model)
            if department:
                queryset = queryset.filter(job_title__icontains=department)
            
            # Counts
            total = queryset.count()
            active_count = queryset.filter(user__is_active=True).count()
            inactive_count = queryset.filter(user__is_active=False).count()
            
            # Pagination
            paginator = self.pagination_class()
            paginated_qs = paginator.paginate_queryset(queryset, request)
            
            serializer = UserProfileSerializer(paginated_qs, many=True)
            pagination_data = paginator.get_paginated_response(serializer.data)
            pagination_data["summary"] = {
                "total": total,
                "active": active_count,
                "inactive": inactive_count
            }
            
            return Response({
                "status": status.HTTP_200_OK,
                "message": "Employees fetched successfully",
                "data": pagination_data
            })
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==================== ALL ADMINS UNDER ORGANIZATION ====================

class AllAdminsUnderOrganizationAPIView(APIView):
    """Get all admins under an organization"""
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination
    
    def get(self, request, org_id):
        try:
            organization = get_object_or_404(BaseUserModel, id=org_id, role='organization')
            
            search = request.query_params.get("q", "")
            status_filter = request.query_params.get("status")
            
            queryset = AdminProfile.objects.filter(organization=organization)
            
            # Search
            if search:
                queryset = queryset.filter(
                    Q(admin_name__icontains=search) |
                    Q(user__email__icontains=search) |
                    Q(user__username__icontains=search)
                )
            
            # Status filter
            if status_filter == 'active':
                queryset = queryset.filter(user__is_active=True)
            elif status_filter == 'inactive':
                queryset = queryset.filter(user__is_active=False)
            
            # Counts
            total = queryset.count()
            active_count = queryset.filter(user__is_active=True).count()
            inactive_count = queryset.filter(user__is_active=False).count()
            
            # Pagination
            paginator = self.pagination_class()
            paginated_qs = paginator.paginate_queryset(queryset, request)
            
            serializer = AdminProfileSerializer(paginated_qs, many=True)
            pagination_data = paginator.get_paginated_response(serializer.data)
            pagination_data["summary"] = {
                "total": total,
                "active": active_count,
                "inactive": inactive_count
            }
            
            return Response({
                "status": status.HTTP_200_OK,
                "message": "Admins fetched successfully",
                "data": pagination_data
            })
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==================== ALL EMPLOYEES UNDER ORGANIZATION ====================

class AllEmployeesUnderOrganizationAPIView(APIView):
    """Get all employees under an organization (across all admins)"""
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination
    
    def get(self, request, org_id):
        try:
            organization = get_object_or_404(BaseUserModel, id=org_id, role='organization')
            
            search = request.query_params.get("q", "")
            status_filter = request.query_params.get("status")
            admin_id = request.query_params.get("admin_id")
            designation = request.query_params.get("designation")
            
            queryset = UserProfile.objects.filter(organization=organization)
            
            # Filter by admin
            if admin_id:
                queryset = queryset.filter(admin_id=admin_id)
            
            # Search
            if search:
                queryset = queryset.filter(
                    Q(user_name__icontains=search) |
                    Q(custom_employee_id__icontains=search) |
                    Q(designation__icontains=search) |
                    Q(user__email__icontains=search)
                )
            
            # Status filter
            if status_filter == 'active':
                queryset = queryset.filter(user__is_active=True)
            elif status_filter == 'inactive':
                queryset = queryset.filter(user__is_active=False)
            
            # Designation filter
            if designation:
                queryset = queryset.filter(designation__icontains=designation)
            
            # Counts
            total = queryset.count()
            active_count = queryset.filter(user__is_active=True).count()
            inactive_count = queryset.filter(user__is_active=False).count()
            
            # Group by admin
            admin_wise = {}
            for profile in queryset:
                admin_id = str(profile.admin.id)
                if admin_id not in admin_wise:
                    admin_wise[admin_id] = {
                        "admin_id": admin_id,
                        "admin_name": profile.admin.email,
                        "count": 0
                    }
                admin_wise[admin_id]["count"] += 1
            
            # Pagination
            paginator = self.pagination_class()
            paginated_qs = paginator.paginate_queryset(queryset, request)
            
            serializer = UserProfileSerializer(paginated_qs, many=True)
            pagination_data = paginator.get_paginated_response(serializer.data)
            pagination_data["summary"] = {
                "total": total,
                "active": active_count,
                "inactive": inactive_count,
                "admin_wise": list(admin_wise.values())
            }
            
            return Response({
                "status": status.HTTP_200_OK,
                "message": "Employees fetched successfully",
                "data": pagination_data
            })
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==================== EMPLOYEE DEACTIVATE/ACTIVATE ====================

class EmployeeDeactivateAPIView(APIView):
    """Deactivate/Activate employee"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request, org_id, employee_id):
        try:
            organization = get_object_or_404(BaseUserModel, id=org_id, role='organization')
            employee = get_object_or_404(BaseUserModel, id=employee_id, role='user')
            profile = get_object_or_404(UserProfile, user=employee, organization=organization)
            
            action = request.data.get("action", "deactivate")  # activate or deactivate
            
            if action == "deactivate":
                employee.is_active = False
                message = "Employee deactivated successfully"
            else:
                employee.is_active = True
                message = "Employee activated successfully"
            
            employee.save()
            
            return Response({
                "status": status.HTTP_200_OK,
                "message": message,
                "data": {
                    "employee_id": str(employee.id),
                    "email": employee.email,
                    "is_active": employee.is_active
                }
            })
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==================== EMPLOYEE PROFILE UPDATE ====================

class EmployeeProfileUpdateAPIView(APIView):
    """Update employee profile"""
    permission_classes = [IsAuthenticated]
    
    def put(self, request, org_id, employee_id):
        try:
            organization = get_object_or_404(BaseUserModel, id=org_id, role='organization')
            employee = get_object_or_404(BaseUserModel, id=employee_id, role='user')
            profile = get_object_or_404(UserProfile, user=employee, organization=organization)
            
            data = request.data.copy()
            
            # Update user basic info if provided
            if 'email' in data:
                employee.email = data.pop('email')
            if 'phone_number' in data:
                employee.phone_number = data.pop('phone_number')
            employee.save()
            
            # Update profile
            serializer = UserProfileSerializer(profile, data=data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({
                    "status": status.HTTP_200_OK,
                    "message": "Profile updated successfully",
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
                "message": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==================== EMPLOYEE TRANSFER TO ANOTHER ADMIN ====================

class EmployeeTransferAPIView(APIView):
    """Transfer employee to another admin"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request, org_id):
        try:
            organization = get_object_or_404(BaseUserModel, id=org_id, role='organization')
            
            employee_ids = request.data.get("employee_ids", [])
            new_admin_id = request.data.get("new_admin_id")
            
            if not employee_ids:
                return Response({
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "employee_ids is required"
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if not new_admin_id:
                return Response({
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "new_admin_id is required"
                }, status=status.HTTP_400_BAD_REQUEST)
            
            new_admin = get_object_or_404(BaseUserModel, id=new_admin_id, role='admin')
            new_admin_profile = get_object_or_404(AdminProfile, user=new_admin, organization=organization)
            
            transferred = []
            errors = []
            
            with transaction.atomic():
                for emp_id in employee_ids:
                    try:
                        employee = get_object_or_404(BaseUserModel, id=emp_id, role='user')
                        profile = get_object_or_404(UserProfile, user=employee, organization=organization)
                        
                        old_admin_id = str(profile.admin.id)
                        profile.admin = new_admin
                        profile.save()
                        
                        transferred.append({
                            "employee_id": str(emp_id),
                            "employee_name": profile.user_name,
                            "old_admin_id": old_admin_id,
                            "new_admin_id": str(new_admin_id)
                        })
                    except Exception as e:
                        errors.append({
                            "employee_id": str(emp_id),
                            "error": str(e)
                        })
            
            return Response({
                "status": status.HTTP_200_OK,
                "message": f"Transferred {len(transferred)} employee(s)",
                "transferred": transferred,
                "errors": errors if errors else None
            })
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==================== ADMIN DETAILS CSV ====================

class AdminDetailCSVAPIView(APIView):
    """Download admin details as CSV"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, org_id):
        try:
            organization = get_object_or_404(BaseUserModel, id=org_id, role='organization')
            admins = AdminProfile.objects.filter(organization=organization)
            
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="admin_details_{org_id}.csv"'
            
            writer = csv.writer(response)
            writer.writerow([
                'Admin ID', 'Admin Name', 'Email', 'Username', 'Phone Number',
                'Status', 'Created At'
            ])
            
            for admin in admins:
                writer.writerow([
                    str(admin.id),
                    admin.admin_name,
                    admin.user.email,
                    admin.user.username,
                    admin.user.phone_number or '',
                    'Active' if admin.user.is_active else 'Inactive',
                    admin.created_at.strftime('%Y-%m-%d %H:%M:%S')
                ])
            
            return response
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==================== DEACTIVATE LIST ====================

class DeactivateUserListAPIView(APIView):
    """Get list of deactivated users"""
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination
    
    def get(self, request, org_id, admin_id=None):
        try:
            organization = get_object_or_404(BaseUserModel, id=org_id, role='organization')
            
            if admin_id:
                admin = get_object_or_404(BaseUserModel, id=admin_id, role='admin')
                queryset = UserProfile.objects.filter(
                    organization=organization,
                    admin=admin,
                    user__is_active=False
                )
            else:
                queryset = UserProfile.objects.filter(
                    organization=organization,
                    user__is_active=False
                )
            
            search = request.query_params.get("q", "")
            if search:
                queryset = queryset.filter(
                    Q(user_name__icontains=search) |
                    Q(custom_employee_id__icontains=search) |
                    Q(user__email__icontains=search)
                )
            
            paginator = self.pagination_class()
            paginated_qs = paginator.paginate_queryset(queryset, request)
            
            serializer = UserProfileSerializer(paginated_qs, many=True)
            pagination_data = paginator.get_paginated_response(serializer.data)
            
            return Response({
                "status": status.HTTP_200_OK,
                "message": "Deactivated users fetched successfully",
                "data": pagination_data
            })
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def put(self, request, admin_id):
        """Bulk activate/deactivate users"""
        try:
            admin = get_object_or_404(BaseUserModel, id=admin_id, role='admin')
            
            employee_ids = request.data.get("employee_ids", [])
            action = request.data.get("action", "activate")  # activate or deactivate
            
            if not employee_ids:
                return Response({
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "employee_ids is required"
                }, status=status.HTTP_400_BAD_REQUEST)
            
            updated = []
            errors = []
            
            with transaction.atomic():
                for emp_id in employee_ids:
                    try:
                        employee = get_object_or_404(BaseUserModel, id=emp_id, role='user')
                        profile = get_object_or_404(UserProfile, user=employee, admin=admin)
                        
                        if action == "activate":
                            employee.is_active = True
                        else:
                            employee.is_active = False
                        
                        employee.save()
                        updated.append(str(emp_id))
                    except Exception as e:
                        errors.append({
                            "employee_id": str(emp_id),
                            "error": str(e)
                        })
            
            return Response({
                "status": status.HTTP_200_OK,
                "message": f"{action.capitalize()}d {len(updated)} user(s)",
                "updated": updated,
                "errors": errors if errors else None
            })
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==================== ALL USER LIST INFO ====================

class AllUserListInfoAPIView(APIView):
    """Get all user list information"""
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination
    
    def get(self, request, user_id):
        try:
            user = get_object_or_404(BaseUserModel, id=user_id)
            
            # Determine organization based on user role
            if user.role == 'organization':
                organization = user
            elif user.role == 'admin':
                admin_profile = get_object_or_404(AdminProfile, user=user)
                organization = admin_profile.organization
            elif user.role == 'user':
                user_profile = get_object_or_404(UserProfile, user=user)
                organization = user_profile.organization
            else:
                return Response({
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Invalid user role"
                }, status=status.HTTP_400_BAD_REQUEST)
            
            queryset = UserProfile.objects.filter(organization=organization)
            
            search = request.query_params.get("q", "")
            if search:
                queryset = queryset.filter(
                    Q(user_name__icontains=search) |
                    Q(custom_employee_id__icontains=search) |
                    Q(designation__icontains=search) |
                    Q(user__email__icontains=search)
                )
            
            paginator = self.pagination_class()
            paginated_qs = paginator.paginate_queryset(queryset, request)
            
            serializer = UserProfileSerializer(paginated_qs, many=True)
            pagination_data = paginator.get_paginated_response(serializer.data)
            
            return Response({
                "status": status.HTTP_200_OK,
                "message": "Users fetched successfully",
                "data": pagination_data
            })
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==================== ALL USER DEVICE INFO ====================

class AllUserDeviceInfoAPIView(APIView):
    """Get all user device information"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, user_id):
        try:
            user = get_object_or_404(BaseUserModel, id=user_id)
            
            # Determine organization
            if user.role == 'organization':
                organization = user
            elif user.role == 'admin':
                admin_profile = get_object_or_404(AdminProfile, user=user)
                organization = admin_profile.organization
            elif user.role == 'user':
                user_profile = get_object_or_404(UserProfile, user=user)
                organization = user_profile.organization
            else:
                return Response({
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Invalid user role"
                }, status=status.HTTP_400_BAD_REQUEST)
            
            profiles = UserProfile.objects.filter(organization=organization)
            
            device_info = []
            for profile in profiles:
                device_info.append({
                    "user_id": str(profile.user.id),
                    "user_name": profile.user_name,
                    "email": profile.user.email,
                    "fcm_token": profile.fcm_token or "Not set",
                    "device_binding_enabled": profile.organization.own_organization_profile_setting.device_binding_enabled if hasattr(profile.organization, 'own_organization_profile_setting') else False
                })
            
            return Response({
                "status": status.HTTP_200_OK,
                "message": "Device info fetched successfully",
                "data": device_info,
                "total": len(device_info)
            })
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==================== EMPLOYEE STATUS UPDATE ====================

class EmployeeStatusUpdateAPIView(APIView):
    """Update employee status for a specific date"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request, admin_id, date_str):
        try:
            admin = get_object_or_404(BaseUserModel, id=admin_id, role='admin')
            target_date = date.fromisoformat(date_str)
            
            employee_ids = request.data.get("employee_ids", [])
            status_value = request.data.get("status")  # active, inactive
            
            if not employee_ids:
                return Response({
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "employee_ids is required"
                }, status=status.HTTP_400_BAD_REQUEST)
            
            updated = []
            for emp_id in employee_ids:
                try:
                    employee = get_object_or_404(BaseUserModel, id=emp_id, role='user')
                    profile = get_object_or_404(UserProfile, user=employee, admin=admin)
                    
                    # Update status
                    if status_value == "active":
                        employee.is_active = True
                    else:
                        employee.is_active = False
                    
                    employee.save()
                    updated.append(str(emp_id))
                except Exception as e:
                    continue
            
            return Response({
                "status": status.HTTP_200_OK,
                "message": f"Updated {len(updated)} employee(s) status",
                "updated": updated,
                "date": date_str
            })
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==================== UPDATE ALLOW FENCING ====================

class UpdateAllowFencingAPIView(APIView):
    """Update geo-fencing setting for employee"""
    permission_classes = [IsAuthenticated]
    
    def put(self, request, admin_id, employee_id):
        try:
            admin = get_object_or_404(BaseUserModel, id=admin_id, role='admin')
            employee = get_object_or_404(BaseUserModel, id=employee_id, role='user')
            profile = get_object_or_404(UserProfile, user=employee, admin=admin)
            
            allow_geo_fencing = request.data.get("allow_geo_fencing", False)
            radius = request.data.get("radius")
            
            profile.allow_geo_fencing = allow_geo_fencing
            if radius:
                profile.radius = radius
            profile.save()
            
            return Response({
                "status": status.HTTP_200_OK,
                "message": "Geo-fencing updated successfully",
                "data": {
                    "employee_id": str(employee.id),
                    "allow_geo_fencing": profile.allow_geo_fencing,
                    "radius": profile.radius
                }
            })
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==================== ALL EMPLOYEE PROFILE ====================

class AllEmployeeProfileAPIView(APIView):
    """Get all employee profiles"""
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination
    
    def get(self, request, admin_id):
        try:
            admin = get_object_or_404(BaseUserModel, id=admin_id, role='admin')
            
            queryset = UserProfile.objects.filter(admin=admin)
            
            search = request.query_params.get("q", "")
            if search:
                queryset = queryset.filter(
                    Q(user_name__icontains=search) |
                    Q(custom_employee_id__icontains=search) |
                    Q(designation__icontains=search) |
                    Q(user__email__icontains=search)
                )
            
            paginator = self.pagination_class()
            paginated_qs = paginator.paginate_queryset(queryset, request)
            
            serializer = UserProfileSerializer(paginated_qs, many=True)
            pagination_data = paginator.get_paginated_response(serializer.data)
            
            return Response({
                "status": status.HTTP_200_OK,
                "message": "Employee profiles fetched successfully",
                "data": pagination_data
            })
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==================== EMPLOYEE BULK DEACTIVATE ====================

class EmployeeBulkDeactivateAPIView(APIView):
    """Bulk deactivate employees"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request, admin_id):
        try:
            admin = get_object_or_404(BaseUserModel, id=admin_id, role='admin')
            
            employee_ids = request.data.get("employee_ids", [])
            action = request.data.get("action", "deactivate")  # activate or deactivate
            
            if not employee_ids:
                return Response({
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "employee_ids is required"
                }, status=status.HTTP_400_BAD_REQUEST)
            
            updated = []
            errors = []
            
            with transaction.atomic():
                for emp_id in employee_ids:
                    try:
                        employee = get_object_or_404(BaseUserModel, id=emp_id, role='user')
                        profile = get_object_or_404(UserProfile, user=employee, admin=admin)
                        
                        if action == "deactivate":
                            employee.is_active = False
                        else:
                            employee.is_active = True
                        
                        employee.save()
                        updated.append({
                            "employee_id": str(emp_id),
                            "employee_name": profile.user_name,
                            "status": "deactivated" if action == "deactivate" else "activated"
                        })
                    except Exception as e:
                        errors.append({
                            "employee_id": str(emp_id),
                            "error": str(e)
                        })
            
            return Response({
                "status": status.HTTP_200_OK,
                "message": f"{action.capitalize()}d {len(updated)} employee(s)",
                "updated": updated,
                "errors": errors if errors else None
            })
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==================== EMPLOYEE GLOBAL SEARCH ====================

class EmployeeGlobalSearchAPIView(APIView):
    """Global search for employees across organization"""
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination
    
    def get(self, request, org_id):
        try:
            organization = get_object_or_404(BaseUserModel, id=org_id, role='organization')
            
            search = request.query_params.get("q", "")
            if not search:
                return Response({
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Search query 'q' is required"
                }, status=status.HTTP_400_BAD_REQUEST)
            
            queryset = UserProfile.objects.filter(organization=organization).filter(
                Q(user_name__icontains=search) |
                Q(custom_employee_id__icontains=search) |
                Q(designation__icontains=search) |
                Q(job_title__icontains=search) |
                Q(user__email__icontains=search) |
                Q(user__username__icontains=search) |
                Q(aadhaar_number__icontains=search) |
                Q(pan_number__icontains=search)
            )
            
            paginator = self.pagination_class()
            paginated_qs = paginator.paginate_queryset(queryset, request)
            
            serializer = UserProfileSerializer(paginated_qs, many=True)
            pagination_data = paginator.get_paginated_response(serializer.data)
            
            return Response({
                "status": status.HTTP_200_OK,
                "message": f"Found {queryset.count()} result(s)",
                "data": pagination_data
            })
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

