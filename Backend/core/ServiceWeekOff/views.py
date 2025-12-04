from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import WeekOffPolicy
from AuthN.models import AdminProfile
from .serializers import WeekOffPolicySerializer, WeekOffPolicyUpdateSerializer


class WeekOffPolicyAPIView(APIView):
    def get(self, request, admin_id, pk=None):
        if pk:
            obj = get_object_or_404(WeekOffPolicy, admin__id=admin_id, id=pk, is_active=True)
            return Response({
                "status": status.HTTP_200_OK,
                "message": "Week off policy fetched successfully",
                "data": WeekOffPolicySerializer(obj).data
            })
        policies = WeekOffPolicy.objects.filter(admin__id=admin_id, is_active=True)
        return Response({
            "status": status.HTTP_200_OK,
            "message": "Week off policies fetched successfully",
            "data": WeekOffPolicySerializer(policies, many=True).data
        })

    def post(self, request, admin_id, pk=None):
        from AuthN.models import BaseUserModel
        admin = get_object_or_404(BaseUserModel, id=admin_id, role='admin')
        data = request.data.copy()
        data['admin'] = str(admin.id)

        serializer = WeekOffPolicySerializer(data=data)
        if serializer.is_valid():
            policy = serializer.save()
            policy_name = policy.name or "Week Off Policy"
            return Response({
                "status": status.HTTP_201_CREATED,
                "message": f"Week off policy '{policy_name}' created successfully",
                "data": serializer.data
            }, status=status.HTTP_201_CREATED)
        return Response({
            "status": status.HTTP_400_BAD_REQUEST,
            "message": "Validation failed",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, admin_id, pk):
        obj = get_object_or_404(WeekOffPolicy, admin__id=admin_id, id=pk)
        serializer = WeekOffPolicyUpdateSerializer(obj, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "status": status.HTTP_200_OK,
                "message": "Week off policy updated successfully",
                "data": serializer.data
            })
        return Response({
            "status": status.HTTP_400_BAD_REQUEST,
            "message": "Validation failed",
            "data": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, admin_id, pk):
        obj = get_object_or_404(WeekOffPolicy, admin__id=admin_id, id=pk)
        
        # Check if week off policy is assigned to any user
        from AuthN.models import UserProfile
        assigned_users = UserProfile.objects.filter(
            week_offs=obj
        ).values_list('user_id', flat=True).distinct()
        
        assigned_count = assigned_users.count()
        
        if assigned_count > 0:
            policy_display_name = obj.name or f"Week Off Policy {obj.id}"
            return Response({
                "status": status.HTTP_400_BAD_REQUEST,
                "message": f"❌ Cannot delete '{policy_display_name}'. This week off policy is currently assigned to {assigned_count} employee(s). Please unassign this policy from all employees before deleting.",
                "data": {
                    "assigned_employees_count": assigned_count,
                    "policy_name": policy_display_name
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Safe to delete
        policy_name = obj.name or "Week Off Policy"
        obj.is_active = False
        obj.save()
        return Response({
            "status": status.HTTP_200_OK,
            "message": f"✅ Week off policy '{policy_name}' deleted successfully",
            "data": None
        })


class AssignWeekOffToUserAPIView(APIView):
    """Assign/Get/Delete week off policies for a user"""
    
    def post(self, request, admin_id, user_id):
        """Assign week off policies to user"""
        from AuthN.models import BaseUserModel, UserProfile
        
        # Validate admin
        admin = get_object_or_404(BaseUserModel, id=admin_id, role='admin')
        
        # Validate user
        user = get_object_or_404(BaseUserModel, id=user_id, role='user')
        user_profile = get_object_or_404(UserProfile, user=user)
        
        # Get week_off_ids from request
        week_off_ids = request.data.get('week_off_ids', [])
        
        if not isinstance(week_off_ids, list):
            return Response({
                "status": status.HTTP_400_BAD_REQUEST,
                "message": "week_off_ids must be an array",
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate week offs belong to admin
        week_offs = WeekOffPolicy.objects.filter(
            id__in=week_off_ids,
            admin=admin,
            is_active=True
        )
        
        if week_offs.count() != len(week_off_ids):
            return Response({
                "status": status.HTTP_400_BAD_REQUEST,
                "message": "Some week off IDs are invalid or not found",
                "data": {
                    "requested": len(week_off_ids),
                    "found": week_offs.count()
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Set week offs for user (replaces existing with new selection)
        user_profile.week_offs.set(week_offs)
        
        # Get assigned week offs data
        from .serializers import WeekOffPolicySerializer
        assigned_week_offs = WeekOffPolicySerializer(user_profile.week_offs.all(), many=True).data
        
        return Response({
            "status": status.HTTP_200_OK,
            "message": f"Successfully assigned {len(assigned_week_offs)} week off policy(ies) to {user_profile.user_name}",
            "data": {
                "user_id": str(user_id),
                "user_name": user_profile.user_name,
                "assigned_week_offs": assigned_week_offs
            }
        }, status=status.HTTP_200_OK)
    
    def get(self, request, admin_id, user_id):
        """Get user's assigned week offs"""
        from AuthN.models import BaseUserModel, UserProfile
        
        # Validate admin
        admin = get_object_or_404(BaseUserModel, id=admin_id, role='admin')
        
        # Validate user
        user = get_object_or_404(BaseUserModel, id=user_id, role='user')
        user_profile = get_object_or_404(UserProfile, user=user)
        
        # Get assigned week offs
        from .serializers import WeekOffPolicySerializer
        assigned_week_offs = WeekOffPolicySerializer(user_profile.week_offs.all(), many=True).data
        
        return Response({
            "status": status.HTTP_200_OK,
            "message": "Week offs fetched successfully",
            "data": {
                "user_id": str(user_id),
                "user_name": user_profile.user_name,
                "assigned_week_offs": assigned_week_offs,
                "count": len(assigned_week_offs)
            }
        }, status=status.HTTP_200_OK)
    
    def delete(self, request, admin_id, user_id, week_off_id=None):
        """Remove specific week off or all week offs from user"""
        from AuthN.models import BaseUserModel, UserProfile
        
        print(f"🔍 DELETE called with: admin_id={admin_id}, user_id={user_id}, week_off_id={week_off_id}")
        
        # Validate admin
        admin = get_object_or_404(BaseUserModel, id=admin_id, role='admin')
        
        # Validate user
        user = get_object_or_404(BaseUserModel, id=user_id, role='user')
        user_profile = get_object_or_404(UserProfile, user=user)
        
        if week_off_id:
            print(f"✅ Removing SPECIFIC week off: {week_off_id}")
        else:
            print(f"⚠️ Removing ALL week offs (week_off_id is None)")
        
        if week_off_id:
            # Remove specific week off
            week_off = get_object_or_404(WeekOffPolicy, id=week_off_id, admin=admin)
            
            if week_off in user_profile.week_offs.all():
                user_profile.week_offs.remove(week_off)
                return Response({
                    "status": status.HTTP_200_OK,
                    "message": f"Removed week off policy '{week_off.name}' from {user_profile.user_name}",
                    "data": {
                        "user_id": str(user_id),
                        "user_name": user_profile.user_name,
                        "week_off_id": week_off_id,
                        "week_off_name": week_off.name
                    }
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    "status": status.HTTP_404_NOT_FOUND,
                    "message": f"Week off policy '{week_off.name}' is not assigned to {user_profile.user_name}",
                    "data": None
                }, status=status.HTTP_404_NOT_FOUND)
        else:
            # Clear all week offs
            week_off_count = user_profile.week_offs.count()
            user_profile.week_offs.clear()
            
            return Response({
                "status": status.HTTP_200_OK,
                "message": f"Removed {week_off_count} week off policy(ies) from {user_profile.user_name}",
                "data": {
                    "user_id": str(user_id),
                    "user_name": user_profile.user_name,
                    "removed_count": week_off_count
                }
            }, status=status.HTTP_200_OK)
