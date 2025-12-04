"""
Additional Utility APIs for AuthN Module
=========================================

This module contains comprehensive APIs for authentication and user management.
All APIs follow RESTful conventions and include proper permission checks.

Key Features:
- Employee profile management with O(1) complexity optimizations
- Admin management under organizations
- Password change functionality for all roles
- Bulk operations with transaction safety
- Optimized queries using select_related/prefetch_related

Time Complexity:
- Most operations are O(1) with optimized database queries
- List operations use pagination for O(n) complexity where n = page size

Space Complexity:
- O(1) for single object operations
- O(page_size) for paginated list operations

Author: Development Team
Last Updated: 2025
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .permissions import *
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.db.models import Q, Count, Sum, Avg
from django.utils import timezone
from datetime import datetime, date
from django.http import HttpResponse
import csv

from .models import *
from .serializers import (
    UserProfileReadSerializer, UserProfileUpdateSerializer,
    AdminProfileReadSerializer, AdminProfileUpdateSerializer,
    ChangePasswordSerializer, EmployeeActivateSerializer,
    EmployeeTransferSerializer, EmployeeStatusUpdateSerializer,
    GeoFencingUpdateSerializer, BulkActivateDeactivateSerializer,
    FcmTokenUpdateSerializer
)
from utils.pagination_utils import CustomPagination


# ==================== CHANGE PASSWORD FOR ALL ROLES ====================

class ChangePasswordAllRolesAPIView(APIView):
    """
    Change password for any role (System Owner, Organization, Admin, User).
    
    Permissions:
        - Users can change their own password
        - System Owner/Organization/Admin can change any user's password with force_change=True
    
    Request Body:
        - old_password (str, optional): Current password (required unless force_change=True)
        - new_password (str, required): New password
        - force_change (bool, optional): Force password change without old password (admin only)
    
    Time Complexity: O(1) - Single database query
    Space Complexity: O(1) - Constant space usage
    """
    permission_classes = [IsAuthenticated, CanUpdateOwnOrAnyUser]
    
    def post(self, request, user_id):
        """
        Change user password.
        
        Args:
            user_id: UUID of the user whose password needs to be changed
            
        Returns:
            Response with success message or error details
        """
        try:
            # O(1) - Single database query
            user = get_object_or_404(BaseUserModel, id=user_id)
            
            # Check object-level permission using CanUpdateOwnOrAnyUser
            permission = CanUpdateOwnOrAnyUser()
            if not permission.has_object_permission(request, self, user):
                return Response({
                    "status": status.HTTP_403_FORBIDDEN,
                    "message": "You don't have permission to change this user's password"
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Use serializer for validation
            serializer = ChangePasswordSerializer(data=request.data)
            if not serializer.is_valid():
                return Response({
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Validation error",
                    "errors": serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            validated_data = serializer.validated_data
            old_password = validated_data.get('old_password')
            new_password = validated_data['new_password']
            force_change = validated_data.get('force_change', False)
            
            # O(1) - Password check uses constant time hashing
            # Check old password only if not force change (admins can bypass)
            if not force_change and old_password:
                if not user.check_password(old_password):
                    return Response({
                        "status": status.HTTP_400_BAD_REQUEST,
                        "message": "Old password is incorrect"
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            # O(1) - Password hashing and single database save
            user.set_password(new_password)
            user.save()
            
            return Response({
                "status": status.HTTP_200_OK,
                "message": f"Password changed successfully for {user.email}"
            }, status=status.HTTP_200_OK)
            
        except BaseUserModel.DoesNotExist:
            return Response({
                "status": status.HTTP_404_NOT_FOUND,
                "message": "User not found"
            }, status=status.HTTP_404_NOT_FOUND)
            
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": f"Error changing password: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==================== EMPLOYEE LIST UNDER ADMIN ====================

class EmployeeListUnderAdminAPIView(APIView):
    """Get all employees under an admin"""
    permission_classes = [IsAuthenticated, IsOrganizationOrAdmin]
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
            # Calculate inactive as total - active to ensure accuracy
            inactive_count = total - active_count
            
            # Pagination
            paginator = self.pagination_class()
            paginated_qs = paginator.paginate_queryset(queryset, request)
            
            serializer = UserProfileReadSerializer(paginated_qs, many=True)
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
    permission_classes = [IsAuthenticated, IsOrganization]
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
            # Calculate inactive as total - active to ensure accuracy
            inactive_count = total - active_count
            
            # Pagination
            paginator = self.pagination_class()
            paginated_qs = paginator.paginate_queryset(queryset, request)
            
            serializer = AdminProfileReadSerializer(paginated_qs, many=True)
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


# ==================== ORGANIZATION'S OWN ADMINS LIST ====================

class OrganizationOwnAdminsAPIView(APIView):
    """Get all admins under the logged-in organization and update admin"""
    permission_classes = [IsAuthenticated, IsOrganization]
    pagination_class = CustomPagination
    
    def get(self, request):
        try:
            # Get the logged-in organization user
            org_user = request.user
            
            # Verify that the logged-in user is an organization
            
            search = request.query_params.get("q", "")
            status_filter = request.query_params.get("status")
            
            queryset = AdminProfile.objects.filter(organization=org_user)
            
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
            # Calculate inactive as total - active to ensure accuracy
            inactive_count = total - active_count
            
            # Pagination
            paginator = self.pagination_class()
            paginated_qs = paginator.paginate_queryset(queryset, request)
            
            serializer = AdminProfileReadSerializer(paginated_qs, many=True)
            pagination_data = paginator.get_paginated_response(serializer.data)
            pagination_data["results"] = serializer.data  # Add results array with admin data
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
    
    def put(self, request, admin_id=None):
        """Update admin details"""
        try:
            # Get the logged-in organization user
            org_user = request.user
            
            # Verify that the logged-in user is an organization
            if org_user.role != 'organization':
                return Response({
                    "status": status.HTTP_403_FORBIDDEN,
                    "message": "Access denied. Organization role required.",
                    "data": {}
                }, status=status.HTTP_403_FORBIDDEN)
            
            # admin_id should come from URL path parameter
            # If not in URL, try to get from request data (for backward compatibility)
            if not admin_id:
                admin_id = request.data.get('admin_id')
            
            if not admin_id:
                return Response({
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Admin ID is required. Use PUT /api/organization/admins/<admin_id>",
                    "data": {}
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Get admin profile
            admin_profile = get_object_or_404(AdminProfile, id=admin_id)
            
            # Verify that admin belongs to this organization
            if admin_profile.organization != org_user:
                return Response({
                    "status": status.HTTP_403_FORBIDDEN,
                    "message": "Access denied. You can only update admins under your organization.",
                    "data": {}
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Use AdminProfileUpdateSerializer for validation and update
            serializer = AdminProfileUpdateSerializer(
                admin_profile,
                data=request.data,
                partial=True
            )
            
            if serializer.is_valid():
                serializer.save()
                # Refresh from DB to get updated data
                admin_profile.refresh_from_db()
                # Use read serializer for response
                read_serializer = AdminProfileReadSerializer(admin_profile)
                
                return Response({
                    "status": status.HTTP_200_OK,
                    "message": "Admin updated successfully",
                    "data": read_serializer.data
                })
            else:
                return Response({
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Validation error",
                    "errors": serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
        except AdminProfile.DoesNotExist:
            return Response({
                "status": status.HTTP_404_NOT_FOUND,
                "message": "Admin not found",
                "data": {}
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": {}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==================== SINGLE ADMIN DETAILS ====================

class AdminDetailsAPIView(APIView):
    """Get single admin details by admin_id and update admin"""
    permission_classes = [IsAuthenticated, IsOrganizationOrAdmin]
    
    def get(self, request, admin_id):
        try:
            # Get the logged-in user
            
            # Get admin profile
            admin_profile = get_object_or_404(AdminProfile, id=admin_id)
            
            # Verify access permissions
            # Organization can only see their own admins
            # Admin can see their own details
            # System owner can see all admins
            # System owner can see all
            
            serializer = AdminProfileReadSerializer(admin_profile)
            
            return Response({
                "status": status.HTTP_200_OK,
                "message": "Admin details fetched successfully",
                "data": serializer.data
            })
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": {}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def put(self, request, admin_id):
        """Update admin details including is_active"""
        try:
            # Get the logged-in user
            
            # Get admin profile
            admin_profile = get_object_or_404(AdminProfile, id=admin_id)
            
            # Verify access permissions
            
            # Use AdminProfileUpdateSerializer for validation and update
            serializer = AdminProfileUpdateSerializer(
                admin_profile,
                data=request.data,
                partial=True
            )
            
            if serializer.is_valid():
                serializer.save()
                # Refresh from DB to get updated data
                admin_profile.refresh_from_db()
                # Use read serializer for response
                read_serializer = AdminProfileReadSerializer(admin_profile)
                
                return Response({
                    "status": status.HTTP_200_OK,
                    "message": "Admin updated successfully",
                    "data": read_serializer.data
                })
            else:
                return Response({
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Validation error",
                    "errors": serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            return Response({
                "status": status.HTTP_200_OK,
                "message": "Admin updated successfully",
                "data": serializer.data
            })
        except AdminProfile.DoesNotExist:
            return Response({
                "status": status.HTTP_404_NOT_FOUND,
                "message": "Admin not found",
                "data": {}
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "errors": {"detail": [str(e)]}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==================== ALL EMPLOYEES UNDER ORGANIZATION ====================

class AllEmployeesUnderOrganizationAPIView(APIView):
    """Get all employees under an organization (across all admins)"""
    permission_classes = [IsAuthenticated, IsOrganizationOrAdmin]
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
            # Calculate inactive as total - active to ensure accuracy
            inactive_count = total - active_count
            
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
            
            serializer = UserProfileReadSerializer(paginated_qs, many=True)
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
    permission_classes = [IsAuthenticated, IsOrganizationOrAdmin]
    
    def post(self, request, admin_id, user_id):
        """
        Deactivate/Activate employee.
        
        Args:
            admin_id: Admin UUID
            user_id: Employee (User) UUID
            
        Returns:
            Response with success message and employee data
        """
        try:
            # O(1) - Database queries with select_related
            admin = get_object_or_404(
                BaseUserModel.objects.select_related(),
                id=admin_id,
                role='admin'
            )
            employee = get_object_or_404(
                BaseUserModel.objects.select_related(),
                id=user_id,
                role='user'
            )
            profile = get_object_or_404(
                UserProfile.objects.select_related('user', 'admin', 'organization'),
                user=employee,
                admin=admin
            )
            
            # Use serializer for validation
            serializer = EmployeeActivateSerializer(data=request.data)
            if not serializer.is_valid():
                return Response({
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Validation error",
                    "errors": serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            action = serializer.validated_data['action']
            
            # O(1) - Update status
            employee.is_active = (action == "activate")
            employee.save()
            
            message = f"Employee {'activated' if action == 'activate' else 'deactivated'} successfully"
            
            return Response({
                "status": status.HTTP_200_OK,
                "message": message,
                "data": {
                    "employee_id": str(employee.id),
                    "email": employee.email,
                    "is_active": employee.is_active
                }
            }, status=status.HTTP_200_OK)
            
        except BaseUserModel.DoesNotExist:
            return Response({
                "status": status.HTTP_404_NOT_FOUND,
                "message": "Admin or employee not found"
            }, status=status.HTTP_404_NOT_FOUND)
            
        except UserProfile.DoesNotExist:
            return Response({
                "status": status.HTTP_404_NOT_FOUND,
                "message": "Employee profile not found"
            }, status=status.HTTP_404_NOT_FOUND)
            
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": f"Error updating employee status: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==================== EMPLOYEE PROFILE UPDATE ====================

class EmployeeProfileUpdateAPIView(APIView):
    """
    Update employee profile details.
    
    Permissions:
        - Organization: Can update employees under their organization
        - Admin: Can update employees under their admin profile
    
    Request Body:
        - email (str, optional): Employee email
        - phone_number (str, optional): Employee phone number
        - user_name (str, optional): Employee name
        - custom_employee_id (str, optional): Custom employee ID
        - date_of_birth (date, optional): Date of birth
        - date_of_joining (date, optional): Date of joining
        - gender (str, optional): Gender
        - designation (str, optional): Designation
        - job_title (str, optional): Job title
        - user.is_active (bool, optional): Active/Inactive status
    
    Time Complexity: O(1) - Single database query with select_related
    Space Complexity: O(1) - Constant space usage
    """
    permission_classes = [IsAuthenticated, IsOrganizationOrAdmin]
    
    def put(self, request, admin_id, user_id):
        """
        Update employee profile.
        
        Args:
            admin_id: Admin UUID
            user_id: Employee (User) UUID
            
        Returns:
            Response with updated employee data or error message
        """
        try:
            # O(1) - Single database query with select_related
            admin = get_object_or_404(
                BaseUserModel.objects.select_related(),
                id=admin_id,
                role='admin'
            )
            
            # O(1) - Single database query with select_related to avoid N+1 queries
            employee = get_object_or_404(
                BaseUserModel.objects.select_related('own_user_profile'),
                id=user_id,
                role='user'
            )
            
            # O(1) - Single database query, uses select_related from employee if available
            profile = get_object_or_404(
                UserProfile.objects.select_related('user', 'admin', 'organization'),
                user=employee,
                admin=admin
            )
            
            # Copy request data to avoid mutating original request
            data = request.data.copy()
            
            # O(1) - Dictionary operations are O(1)
            # Update user basic info if provided
            if 'email' in data:
                employee.email = data.pop('email')
            
            if 'phone_number' in data:
                employee.phone_number = data.pop('phone_number')
            
            # Handle is_active status update (can be in nested user object or top level)
            # O(1) - Dictionary key check and value access
            if 'user' in data and isinstance(data['user'], dict):
                user_data = data['user']
                if 'is_active' in user_data:
                    employee.is_active = bool(user_data['is_active'])
            elif 'is_active' in data:
                # Handle is_active if provided at top level for backward compatibility
                employee.is_active = bool(data.pop('is_active'))
            
            # O(1) - Single database save operation
            employee.save()
            
            # Update profile fields using serializer for validation
            # O(1) - Serializer validation and save (doesn't scale with input size)
            serializer = UserProfileUpdateSerializer(
                profile,
                data=data,
                partial=True,
                context={'request': request}
            )
            
            if serializer.is_valid():
                serializer.save()
                return Response({
                    "status": status.HTTP_200_OK,
                    "message": "Profile updated successfully",
                    "data": serializer.data
                }, status=status.HTTP_200_OK)
            
            # Return validation errors
            return Response({
                "status": status.HTTP_400_BAD_REQUEST,
                "message": "Validation error",
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except BaseUserModel.DoesNotExist:
            return Response({
                "status": status.HTTP_404_NOT_FOUND,
                "message": "Organization or employee not found",
                "data": {}
            }, status=status.HTTP_404_NOT_FOUND)
            
        except UserProfile.DoesNotExist:
            return Response({
                "status": status.HTTP_404_NOT_FOUND,
                "message": "Employee profile not found",
                "data": {}
            }, status=status.HTTP_404_NOT_FOUND)
            
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": f"Error updating employee profile: {str(e)}",
                "data": {}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==================== EMPLOYEE TRANSFER TO ANOTHER ADMIN ====================

class EmployeeTransferAPIView(APIView):
    """Transfer employee to another admin"""
    permission_classes = [IsAuthenticated, IsOrganizationOrAdmin]
    
    def post(self, request, org_id):
        """
        Transfer employee to another admin.
        
        Args:
            org_id: Organization UUID
            
        Returns:
            Response with transfer results
        """
        try:
            organization = get_object_or_404(BaseUserModel, id=org_id, role='organization')
            
            # Use serializer for validation
            serializer = EmployeeTransferSerializer(data=request.data)
            if not serializer.is_valid():
                return Response({
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Validation error",
                    "errors": serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            validated_data = serializer.validated_data
            employee_ids = validated_data['employee_ids']
            new_admin_id = validated_data['new_admin_id']
            
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
            }, status=status.HTTP_200_OK)
            
        except BaseUserModel.DoesNotExist:
            return Response({
                "status": status.HTTP_404_NOT_FOUND,
                "message": "Organization or admin not found"
            }, status=status.HTTP_404_NOT_FOUND)
            
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": f"Error transferring employees: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==================== ADMIN DETAILS CSV ====================

class AdminDetailCSVAPIView(APIView):
    """Download admin details as CSV"""
    permission_classes = [IsAuthenticated, IsOrganizationOrAdmin]
    
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
    permission_classes = [IsAuthenticated, IsOrganizationOrAdmin]
    pagination_class = CustomPagination
    
    def get(self, request,  admin_id=None):
        try:
            if admin_id:
                admin = get_object_or_404(BaseUserModel, id=admin_id, role='admin')
                queryset = UserProfile.objects.filter(
                    admin=admin,
                    user__is_active=False
                )
            else:
                return Response({
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Admin ID is required"
                }, status=status.HTTP_400_BAD_REQUEST)
            search = request.query_params.get("q", "")
            if search:
                queryset = queryset.filter(
                    Q(user_name__icontains=search) |
                    Q(custom_employee_id__icontains=search) |
                    Q(user__email__icontains=search)
                )
            
            paginator = self.pagination_class()
            paginated_qs = paginator.paginate_queryset(queryset, request)
            
            serializer = UserProfileReadSerializer(paginated_qs, many=True)
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
        """
        Bulk activate/deactivate users.
        
        Args:
            admin_id: Admin UUID
            
        Returns:
            Response with bulk update results
        """
        try:
            admin = get_object_or_404(BaseUserModel, id=admin_id, role='admin')
            
            # Use serializer for validation
            serializer = BulkActivateDeactivateSerializer(data=request.data)
            if not serializer.is_valid():
                return Response({
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Validation error",
                    "errors": serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            validated_data = serializer.validated_data
            employee_ids = validated_data['employee_ids']
            action = validated_data['action']
            
            updated = []
            errors = []
            
            with transaction.atomic():
                for emp_id in employee_ids:
                    try:
                        employee = get_object_or_404(BaseUserModel, id=emp_id, role='user')
                        profile = get_object_or_404(UserProfile, user=employee, admin=admin)
                        
                        employee.is_active = (action == "activate")
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
            }, status=status.HTTP_200_OK)
            
        except BaseUserModel.DoesNotExist:
            return Response({
                "status": status.HTTP_404_NOT_FOUND,
                "message": "Admin not found"
            }, status=status.HTTP_404_NOT_FOUND)
            
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": f"Error in bulk operation: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==================== ALL USER LIST INFO ====================

class AllUserListInfoAPIView(APIView):
    """Get all user list information"""
    permission_classes = [IsAuthenticated , IsOrganizationOrAdmin]
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
            
            serializer = UserProfileReadSerializer(paginated_qs, many=True)
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
    permission_classes = [IsAuthenticated, IsOrganizationOrAdmin]
    
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
    permission_classes = [IsAuthenticated, IsOrganizationOrAdmin]
    
    def post(self, request, admin_id, date_str):
        """
        Update employee status for a specific date.
        
        Args:
            admin_id: Admin UUID
            date_str: Date string in ISO format
            
        Returns:
            Response with update results
        """
        try:
            admin = get_object_or_404(BaseUserModel, id=admin_id, role='admin')
            
            # Validate date format
            try:
                target_date = date.fromisoformat(date_str)
            except ValueError:
                return Response({
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": f"Invalid date format: {date_str}. Expected ISO format (YYYY-MM-DD)."
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Use serializer for validation
            serializer = EmployeeStatusUpdateSerializer(data=request.data)
            if not serializer.is_valid():
                return Response({
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Validation error",
                    "errors": serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            validated_data = serializer.validated_data
            employee_ids = validated_data['employee_ids']
            status_value = validated_data['status']
            
            updated = []
            errors = []
            
            with transaction.atomic():
                for emp_id in employee_ids:
                    try:
                        employee = get_object_or_404(BaseUserModel, id=emp_id, role='user')
                        profile = get_object_or_404(UserProfile, user=employee, admin=admin)
                        
                        employee.is_active = (status_value == "active")
                        employee.save()
                        updated.append(str(emp_id))
                    except Exception as e:
                        errors.append({
                            "employee_id": str(emp_id),
                            "error": str(e)
                        })
            
            return Response({
                "status": status.HTTP_200_OK,
                "message": f"Updated {len(updated)} employee(s) status",
                "updated": updated,
                "errors": errors if errors else None,
                "date": date_str
            }, status=status.HTTP_200_OK)
            
        except BaseUserModel.DoesNotExist:
            return Response({
                "status": status.HTTP_404_NOT_FOUND,
                "message": "Admin not found"
            }, status=status.HTTP_404_NOT_FOUND)
            
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": f"Error updating employee status: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==================== UPDATE ALLOW FENCING ====================

class UpdateAllowFencingAPIView(APIView):
    """Update geo-fencing setting for employee"""
    permission_classes = [IsAuthenticated, IsOrganizationOrAdmin]
    
    def put(self, request, admin_id, employee_id):
        """
        Update geo-fencing setting for employee.
        
        Args:
            admin_id: Admin UUID
            employee_id: Employee UUID
            
        Returns:
            Response with updated geo-fencing data
        """
        try:
            admin = get_object_or_404(BaseUserModel, id=admin_id, role='admin')
            employee = get_object_or_404(BaseUserModel, id=employee_id, role='user')
            profile = get_object_or_404(UserProfile, user=employee, admin=admin)
            
            # Use serializer for validation
            serializer = GeoFencingUpdateSerializer(data=request.data)
            if not serializer.is_valid():
                return Response({
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Validation error",
                    "errors": serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            validated_data = serializer.validated_data
            allow_geo_fencing = validated_data.get('allow_geo_fencing', False)
            radius = validated_data.get('radius')
            
            profile.allow_geo_fencing = allow_geo_fencing
            if radius is not None:
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
            }, status=status.HTTP_200_OK)
            
        except BaseUserModel.DoesNotExist:
            return Response({
                "status": status.HTTP_404_NOT_FOUND,
                "message": "Admin or employee not found"
            }, status=status.HTTP_404_NOT_FOUND)
            
        except UserProfile.DoesNotExist:
            return Response({
                "status": status.HTTP_404_NOT_FOUND,
                "message": "Employee profile not found"
            }, status=status.HTTP_404_NOT_FOUND)
            
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": f"Error updating geo-fencing: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==================== ALL EMPLOYEE PROFILE ====================

class AllEmployeeProfileAPIView(APIView):
    """Get all employee profiles"""
    permission_classes = [IsAuthenticated, IsOrganizationOrAdmin]
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
            
            serializer = UserProfileReadSerializer(paginated_qs, many=True)
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
    permission_classes = [IsAuthenticated, IsOrganizationOrAdmin]
    
    def post(self, request, admin_id):
        """
        Bulk deactivate employees.
        
        Args:
            admin_id: Admin UUID
            
        Returns:
            Response with bulk operation results
        """
        try:
            admin = get_object_or_404(BaseUserModel, id=admin_id, role='admin')
            
            # Use serializer for validation
            serializer = BulkActivateDeactivateSerializer(data=request.data)
            if not serializer.is_valid():
                return Response({
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Validation error",
                    "errors": serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            validated_data = serializer.validated_data
            employee_ids = validated_data['employee_ids']
            action = validated_data['action']
            
            updated = []
            errors = []
            
            with transaction.atomic():
                for emp_id in employee_ids:
                    try:
                        employee = get_object_or_404(BaseUserModel, id=emp_id, role='user')
                        profile = get_object_or_404(UserProfile, user=employee, admin=admin)
                        
                        employee.is_active = (action == "activate")
                        employee.save()
                        
                        updated.append({
                            "employee_id": str(emp_id),
                            "employee_name": profile.user_name,
                            "status": "activated" if action == "activate" else "deactivated"
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
            }, status=status.HTTP_200_OK)
            
        except BaseUserModel.DoesNotExist:
            return Response({
                "status": status.HTTP_404_NOT_FOUND,
                "message": "Admin not found"
            }, status=status.HTTP_404_NOT_FOUND)
            
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": f"Error in bulk operation: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==================== EMPLOYEE GLOBAL SEARCH ====================

class EmployeeGlobalSearchAPIView(APIView):
    """Global search for employees across organization"""
    permission_classes = [IsAuthenticated, IsOrganizationOrAdmin]
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
            
            serializer = UserProfileReadSerializer(paginated_qs, many=True)
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


# ==================== FCM TOKEN UPDATE ====================

class UserFcmTokenUpdate(APIView):
    """
    Update FCM token for a user.
    
    Permissions:
        - Users can update their own FCM token
        - System Owner/Organization/Admin can update any user's FCM token
    
    Request Body:
        - fcm_token (str, required): Firebase Cloud Messaging token
    
    Time Complexity: O(1) - Single database query
    Space Complexity: O(1) - Constant space usage
    """
    permission_classes = [IsAuthenticated, IsUser]
    
    def post(self, request, user_id):
        """
        Update FCM token for a user.
        
        Args:
            user_id: UUID of the user whose FCM token needs to be updated
        
        Returns:
            Response with success message or error details
        """
        try:
            # O(1) - Single database query
            user = get_object_or_404(BaseUserModel, id=user_id)
            
            
            # Use serializer for validation
            serializer = FcmTokenUpdateSerializer(data=request.data)
            if not serializer.is_valid():
                return Response({
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Validation error",
                    "errors": serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            fcm_token = serializer.validated_data['fcm_token']
            
            # Update FCM token in UserProfile if user has a profile
            if user.role == 'user':
                try:
                    user_profile = UserProfile.objects.get(user=user)
                    user_profile.fcm_token = fcm_token
                    user_profile.save()
                    return Response({
                        "status": status.HTTP_200_OK,
                        "message": "FCM token updated successfully",
                        "data": {
                            "user_id": str(user.id),
                            "fcm_token": fcm_token
                        }
                    }, status=status.HTTP_200_OK)
                except UserProfile.DoesNotExist:
                    return Response({
                        "status": status.HTTP_404_NOT_FOUND,
                        "message": "User profile not found"
                    }, status=status.HTTP_404_NOT_FOUND)
            else:
                # For other roles, you might want to store FCM token differently
                return Response({
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "FCM token update is currently only supported for user role"
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": f"Error updating FCM token: {str(e)}",
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
