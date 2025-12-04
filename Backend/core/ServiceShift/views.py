from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from .models import ServiceShift
from .serializers import *
from django.shortcuts import get_object_or_404
from AuthN.models import *


class ServiceShiftAPIView(APIView):
    def get(self, request, admin_id, pk=None):
        if pk:
            obj = get_object_or_404(ServiceShift, admin__id=admin_id, id=pk, is_active=True)
            return Response({
                "status": status.HTTP_200_OK,
                "message": "Shift fetched successfully",
                "data": ServiceShiftSerializer(obj).data
            })
        shifts = ServiceShift.objects.filter(admin__id=admin_id, is_active=True)
        return Response({
            "status": status.HTTP_200_OK,
            "message": "Shifts fetched successfully",
            "data": ServiceShiftSerializer(shifts, many=True).data
        })

    def post(self, request, admin_id, pk=None):
        admin = get_object_or_404(BaseUserModel, id=admin_id, role='admin')
        data = request.data.copy()
        data['admin'] = str(admin.id)

        serializer = ServiceShiftSerializer(data=data)
        if serializer.is_valid():
            shift = serializer.save()
            return Response({
                "status": status.HTTP_201_CREATED,
                "message": f"Shift '{shift.shift_name}' created successfully",
                "data": serializer.data
            }, status=status.HTTP_201_CREATED)
        return Response({
            "status": status.HTTP_400_BAD_REQUEST,
            "message": "Validation failed",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, admin_id, pk):
        obj = get_object_or_404(ServiceShift, admin__id=admin_id, id=pk)
        serializer = ServiceShiftUpdateSerializer(obj, data=request.data)
        if serializer.is_valid():
            shift = serializer.save()
            return Response({
                "status": status.HTTP_200_OK,
                "message": f"Shift '{shift.shift_name}' updated successfully",
                "data": serializer.data
            })
        return Response({
            "status": status.HTTP_400_BAD_REQUEST,
            "message": "Validation failed",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, admin_id, pk):
        obj = get_object_or_404(ServiceShift, admin__id=admin_id, id=pk)
        
        # Check if shift is assigned to any user
        assigned_users = UserProfile.objects.filter(
            shifts=obj
        ).values_list('user_id', flat=True).distinct()
        
        assigned_count = assigned_users.count()
        
        if assigned_count > 0:
            shift_display_name = obj.shift_name or f"Shift ({obj.start_time} - {obj.end_time})"
            return Response({
                "status": status.HTTP_400_BAD_REQUEST,
                "message": f"❌ Cannot delete '{shift_display_name}'. This shift is currently assigned to {assigned_count} employee(s). Please unassign this shift from all employees before deleting.",
                "data": {
                    "assigned_employees_count": assigned_count,
                    "shift_name": shift_display_name
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Safe to delete
        shift_name = obj.shift_name
        obj.is_active = False
        obj.save()
        return Response({
            "status": status.HTTP_200_OK,
            "message": f"✅ Shift '{shift_name}' deleted successfully",
            "data": None
        })


class AssignShiftToUserAPIView(APIView):
    """
    Assign multiple shifts to a user
    POST /assign-shifts/<admin_id>/<user_id>
    Body: { "shift_ids": [1, 2, 3] }
    """
    
    def post(self, request, admin_id, user_id):
        """Assign shifts to user"""
        # Validate admin
        admin = get_object_or_404(BaseUserModel, id=admin_id, role='admin')
        
        # Validate user
        user = get_object_or_404(BaseUserModel, id=user_id, role='user')
        user_profile = get_object_or_404(UserProfile, user=user)
        
        # Get shift_ids from request
        shift_ids = request.data.get('shift_ids', [])
        
        if not shift_ids:
            return Response({
                "status": status.HTTP_400_BAD_REQUEST,
                "message": "shift_ids are required",
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not isinstance(shift_ids, list):
            return Response({
                "status": status.HTTP_400_BAD_REQUEST,
                "message": "shift_ids must be an array",
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate shifts belong to admin
        shifts = ServiceShift.objects.filter(
            id__in=shift_ids,
            admin=admin,
            is_active=True
        )
        
        if shifts.count() != len(shift_ids):
            return Response({
                "status": status.HTTP_400_BAD_REQUEST,
                "message": "Some shift IDs are invalid or not found",
                "data": {
                    "requested": len(shift_ids),
                    "found": shifts.count()
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Set shifts for user (replaces existing with new selection)
        user_profile.shifts.set(shifts)
        
        # Get assigned shifts data
        assigned_shifts = ServiceShiftSerializer(user_profile.shifts.all(), many=True).data
        
        return Response({
            "status": status.HTTP_200_OK,
            "message": f"Successfully assigned {len(assigned_shifts)} shift(s) to {user_profile.user_name}",
            "data": {
                "user_id": str(user_id),
                "user_name": user_profile.user_name,
                "assigned_shifts": assigned_shifts
            }
        }, status=status.HTTP_200_OK)
    
    def get(self, request, admin_id, user_id):
        """Get user's assigned shifts"""
        # Validate admin
        admin = get_object_or_404(BaseUserModel, id=admin_id, role='admin')
        
        # Validate user
        user = get_object_or_404(BaseUserModel, id=user_id, role='user')
        user_profile = get_object_or_404(UserProfile, user=user)
        
        # Get assigned shifts
        assigned_shifts = ServiceShiftSerializer(user_profile.shifts.all(), many=True).data
        
        return Response({
            "status": status.HTTP_200_OK,
            "message": "Shifts fetched successfully",
            "data": {
                "user_id": str(user_id),
                "user_name": user_profile.user_name,
                "assigned_shifts": assigned_shifts,
                "count": len(assigned_shifts)
            }
        }, status=status.HTTP_200_OK)
    
    def delete(self, request, admin_id, user_id, shift_id=None):
        """Remove specific shift or all shifts from user"""
        from AuthN.models import BaseUserModel, UserProfile
        
        print(f"🔍 DELETE called with: admin_id={admin_id}, user_id={user_id}, shift_id={shift_id}")
        
        # Validate admin
        admin = get_object_or_404(BaseUserModel, id=admin_id, role='admin')
        
        # Validate user
        user = get_object_or_404(BaseUserModel, id=user_id, role='user')
        user_profile = get_object_or_404(UserProfile, user=user)
        
        if shift_id:
            print(f"✅ Removing SPECIFIC shift: {shift_id}")
        else:
            print(f"⚠️ Removing ALL shifts (shift_id is None)")
        
        if shift_id:
            # Remove specific shift
            shift = get_object_or_404(ServiceShift, id=shift_id, admin=admin)
            
            if shift in user_profile.shifts.all():
                user_profile.shifts.remove(shift)
                return Response({
                    "status": status.HTTP_200_OK,
                    "message": f"Removed shift '{shift.shift_name}' from {user_profile.user_name}",
                    "data": {
                        "user_id": str(user_id),
                        "user_name": user_profile.user_name,
                        "shift_id": shift_id,
                        "shift_name": shift.shift_name
                    }
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    "status": status.HTTP_404_NOT_FOUND,
                    "message": f"Shift '{shift.shift_name}' is not assigned to {user_profile.user_name}",
                    "data": None
                }, status=status.HTTP_404_NOT_FOUND)
        else:
            # Clear all shifts
            shift_count = user_profile.shifts.count()
            user_profile.shifts.clear()
            
            return Response({
                "status": status.HTTP_200_OK,
                "message": f"Removed {shift_count} shift(s) from {user_profile.user_name}",
                "data": {
                    "user_id": str(user_id),
                    "user_name": user_profile.user_name,
                    "removed_count": shift_count
                }
            }, status=status.HTTP_200_OK)