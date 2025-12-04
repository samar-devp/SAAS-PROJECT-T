# views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import Location
from AuthN.models import AdminProfile
from .serializers import LocationSerializer

class LocationAPIView(APIView):
    def get(self, request, admin_id, pk=None):
        if pk:
            obj = get_object_or_404(Location, admin__id=admin_id, id=pk, is_active=True)
            return Response({
                "status": status.HTTP_200_OK,
                "message": "Location fetched successfully",
                "data": LocationSerializer(obj).data
            })
        locations = Location.objects.filter(admin__id=admin_id, is_active=True)
        return Response({
            "status": status.HTTP_200_OK,
            "message": "Locations fetched successfully",
            "data": LocationSerializer(locations, many=True).data
        })

    def post(self, request, admin_id, pk=None):
        admin = get_object_or_404(AdminProfile, user_id=admin_id)
        data = request.data.copy()
        data['admin'] = str(admin.user_id)
        data['organization'] = str(admin.organization.id)

        serializer = LocationSerializer(data=data)
        if serializer.is_valid():
            location = serializer.save()
            return Response({
                "status": status.HTTP_201_CREATED,
                "message": f"Location '{location.name}' created successfully",
                "data": serializer.data
            }, status=status.HTTP_201_CREATED)
        return Response({
            "status": status.HTTP_400_BAD_REQUEST,
            "message": "Validation failed",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, admin_id, pk):
        obj = get_object_or_404(Location, admin__id=admin_id, id=pk)
        serializer = LocationSerializer(obj, data=request.data, partial=True)
        if serializer.is_valid():
            location = serializer.save()
            return Response({
                "status": status.HTTP_200_OK,
                "message": f"Location '{location.name}' updated successfully",
                "data": serializer.data
            })
        return Response({
            "status": status.HTTP_400_BAD_REQUEST,
            "message": "Validation failed",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, admin_id, pk):
        obj = get_object_or_404(Location, admin__id=admin_id, id=pk)
        
        # Check if location is assigned to any user
        from AuthN.models import UserProfile
        assigned_users = UserProfile.objects.filter(
            locations=obj
        ).values_list('user_id', flat=True).distinct()
        
        assigned_count = assigned_users.count()
        
        if assigned_count > 0:
            return Response({
                "status": status.HTTP_400_BAD_REQUEST,
                "message": f"❌ Cannot delete '{obj.name}'. This location is currently assigned to {assigned_count} employee(s). Please unassign this location from all employees before deleting.",
                "data": {
                    "assigned_employees_count": assigned_count,
                    "location_name": obj.name
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Safe to delete
        location_name = obj.name
        obj.is_active = False
        obj.save()
        return Response({
            "status": status.HTTP_200_OK,
            "message": f"✅ Location '{location_name}' deleted successfully",
            "data": None
        })


class AssignLocationToUserAPIView(APIView):
    """
    Assign multiple locations to a user
    POST /assign-locations/<admin_id>/<user_id>
    Body: { "location_ids": [1, 2, 3] }
    """
    
    def post(self, request, admin_id, user_id):
        """Assign locations to user"""
        from AuthN.models import BaseUserModel, UserProfile
        
        # Validate admin
        admin = get_object_or_404(BaseUserModel, id=admin_id, role='admin')
        
        # Validate user
        user = get_object_or_404(BaseUserModel, id=user_id, role='user')
        user_profile = get_object_or_404(UserProfile, user=user)
        
        # Get location_ids from request
        location_ids = request.data.get('location_ids', [])
        
        if not location_ids:
            return Response({
                "status": status.HTTP_400_BAD_REQUEST,
                "message": "location_ids are required",
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not isinstance(location_ids, list):
            return Response({
                "status": status.HTTP_400_BAD_REQUEST,
                "message": "location_ids must be an array",
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate locations belong to admin
        locations = Location.objects.filter(
            id__in=location_ids,
            admin=admin,
            is_active=True
        )
        
        if locations.count() != len(location_ids):
            return Response({
                "status": status.HTTP_400_BAD_REQUEST,
                "message": "Some location IDs are invalid or not found",
                "data": {
                    "requested": len(location_ids),
                    "found": locations.count()
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Set locations for user (replaces existing with new selection)
        user_profile.locations.set(locations)
        
        # Get assigned locations data
        assigned_locations = LocationSerializer(user_profile.locations.all(), many=True).data
        
        return Response({
            "status": status.HTTP_200_OK,
            "message": f"Successfully assigned {len(assigned_locations)} location(s) to {user_profile.user_name}",
            "data": {
                "user_id": str(user_id),
                "user_name": user_profile.user_name,
                "assigned_locations": assigned_locations
            }
        }, status=status.HTTP_200_OK)
    
    def get(self, request, admin_id, user_id):
        """Get user's assigned locations"""
        from AuthN.models import BaseUserModel, UserProfile
        
        # Validate admin
        admin = get_object_or_404(BaseUserModel, id=admin_id, role='admin')
        
        # Validate user
        user = get_object_or_404(BaseUserModel, id=user_id, role='user')
        user_profile = get_object_or_404(UserProfile, user=user)
        
        # Get assigned locations
        assigned_locations = LocationSerializer(user_profile.locations.all(), many=True).data
        
        return Response({
            "status": status.HTTP_200_OK,
            "message": "Locations fetched successfully",
            "data": {
                "user_id": str(user_id),
                "user_name": user_profile.user_name,
                "assigned_locations": assigned_locations,
                "count": len(assigned_locations)
            }
        }, status=status.HTTP_200_OK)
    
    def delete(self, request, admin_id, user_id, location_id=None):
        """Remove specific location or all locations from user"""
        from AuthN.models import BaseUserModel, UserProfile
        
        print(f"🔍 DELETE called with: admin_id={admin_id}, user_id={user_id}, location_id={location_id}")
        
        # Validate admin
        admin = get_object_or_404(BaseUserModel, id=admin_id, role='admin')
        
        # Validate user
        user = get_object_or_404(BaseUserModel, id=user_id, role='user')
        user_profile = get_object_or_404(UserProfile, user=user)
        
        if location_id:
            print(f"✅ Removing SPECIFIC location: {location_id}")
        else:
            print(f"⚠️ Removing ALL locations (location_id is None)")
        
        if location_id:
            # Remove specific location
            location = get_object_or_404(Location, id=location_id, admin=admin)
            
            if location in user_profile.locations.all():
                user_profile.locations.remove(location)
                return Response({
                    "status": status.HTTP_200_OK,
                    "message": f"Removed location '{location.name}' from {user_profile.user_name}",
                    "data": {
                        "user_id": str(user_id),
                        "user_name": user_profile.user_name,
                        "location_id": location_id,
                        "location_name": location.name
                    }
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    "status": status.HTTP_404_NOT_FOUND,
                    "message": f"Location '{location.name}' is not assigned to {user_profile.user_name}",
                    "data": None
                }, status=status.HTTP_404_NOT_FOUND)
        else:
            # Clear all locations
            location_count = user_profile.locations.count()
            user_profile.locations.clear()
            
            return Response({
                "status": status.HTTP_200_OK,
                "message": f"Removed {location_count} location(s) from {user_profile.user_name}",
                "data": {
                    "user_id": str(user_id),
                    "user_name": user_profile.user_name,
                    "removed_count": location_count
                }
            }, status=status.HTTP_200_OK)
