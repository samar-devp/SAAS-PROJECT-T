from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from datetime import datetime, timedelta
from django.db.models import Q
from django.shortcuts import get_object_or_404

from .models import UserLocationHistory, UserLiveLocation
from .serializers import (
    UserLocationHistorySerializer,
    UserLiveLocationSerializer,
    LocationUpdateSerializer
)
from AuthN.models import BaseUserModel


class LocationHistoryAPIView(APIView):
    """API to get location history for a user"""
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id):
        """
        Get location history for a user
        Query params:
        - start_date: Start date (YYYY-MM-DD)
        - end_date: End date (YYYY-MM-DD)
        - limit: Number of records to return (default: 100)
        - offset: Offset for pagination (default: 0)
        """
        try:
            # Check if user exists
            user = get_object_or_404(BaseUserModel, id=user_id, role='user')
            
            # Check permissions - admin can view their users, user can view their own
            if request.user.role == 'user' and str(request.user.id) != str(user_id):
                return Response(
                    {"error": "You don't have permission to view this user's location"},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Get query parameters
            start_date = request.query_params.get('start_date')
            end_date = request.query_params.get('end_date')
            limit = int(request.query_params.get('limit', 100))
            offset = int(request.query_params.get('offset', 0))
            
            # Build query
            queryset = UserLocationHistory.objects.filter(user=user)
            
            # Filter by date range
            if start_date:
                try:
                    start_dt = datetime.strptime(start_date, '%Y-%m-%d').date()
                    queryset = queryset.filter(captured_at__date__gte=start_dt)
                except ValueError:
                    pass
            
            if end_date:
                try:
                    end_dt = datetime.strptime(end_date, '%Y-%m-%d').date()
                    queryset = queryset.filter(captured_at__date__lte=end_dt)
                except ValueError:
                    pass
            
            # Order by captured_at descending
            queryset = queryset.order_by('-captured_at')
            
            # Pagination
            total_count = queryset.count()
            queryset = queryset[offset:offset + limit]
            
            # Serialize
            serializer = UserLocationHistorySerializer(queryset, many=True)
            
            return Response({
                "status": status.HTTP_200_OK,
                "message": "Location history fetched successfully",
                "data": serializer.data,
                "total_count": total_count,
                "limit": limit,
                "offset": offset
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class LiveLocationAPIView(APIView):
    """API to get live location of users"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Get live locations
        Query params:
        - user_id: Specific user ID (optional)
        - admin_id: Get all users under admin (for admin role)
        """
        try:
            user_role = request.user.role
            
            if user_role == 'user':
                # User can only see their own live location
                try:
                    live_location = UserLiveLocation.objects.get(user=request.user)
                    serializer = UserLiveLocationSerializer(live_location)
                    return Response({
                        "status": status.HTTP_200_OK,
                        "message": "Live location fetched successfully",
                        "data": [serializer.data]
                    }, status=status.HTTP_200_OK)
                except UserLiveLocation.DoesNotExist:
                    return Response({
                        "status": status.HTTP_404_NOT_FOUND,
                        "message": "Live location not found",
                        "data": []
                    }, status=status.HTTP_404_NOT_FOUND)
            
            elif user_role == 'admin':
                # Admin can see all users under them
                user_id = request.query_params.get('user_id')
                
                if user_id:
                    # Get specific user's live location
                    try:
                        user = BaseUserModel.objects.get(id=user_id, role='user')
                        # Verify user is under this admin
                        user_profile = user.own_user_profile
                        if str(user_profile.admin.id) != str(request.user.id):
                            return Response({
                                "error": "You don't have permission to view this user's location"
                            }, status=status.HTTP_403_FORBIDDEN)
                        
                        live_location = UserLiveLocation.objects.get(user=user)
                        serializer = UserLiveLocationSerializer(live_location)
                        return Response({
                            "status": status.HTTP_200_OK,
                            "message": "Live location fetched successfully",
                            "data": [serializer.data]
                        }, status=status.HTTP_200_OK)
                    except (BaseUserModel.DoesNotExist, UserLiveLocation.DoesNotExist):
                        return Response({
                            "status": status.HTTP_404_NOT_FOUND,
                            "message": "Live location not found",
                            "data": []
                        }, status=status.HTTP_404_NOT_FOUND)
                else:
                    # Get all users under admin
                    from AuthN.models import UserProfile
                    user_profiles = UserProfile.objects.filter(admin=request.user)
                    user_ids = [profile.user.id for profile in user_profiles]
                    
                    live_locations = UserLiveLocation.objects.filter(
                        user_id__in=user_ids,
                        is_online=True
                    ).order_by('-updated_at')
                    
                    serializer = UserLiveLocationSerializer(live_locations, many=True)
                    return Response({
                        "status": status.HTTP_200_OK,
                        "message": "Live locations fetched successfully",
                        "data": serializer.data
                    }, status=status.HTTP_200_OK)
            
            else:
                return Response({
                    "error": "Invalid user role"
                }, status=status.HTTP_403_FORBIDDEN)
                
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class LocationUpdateAPIView(APIView):
    """API endpoint for mobile app to update location (alternative to WebSocket)"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Update user location"""
        try:
            if request.user.role != 'user':
                return Response({
                    "error": "Only users can update their location"
                }, status=status.HTTP_403_FORBIDDEN)
            
            serializer = LocationUpdateSerializer(data=request.data)
            if not serializer.is_valid():
                return Response({
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Invalid data",
                    "errors": serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            location_data = serializer.validated_data
            
            # Get admin and organization from user profile
            admin = None
            organization = None
            try:
                user_profile = request.user.own_user_profile
                admin = user_profile.admin
                organization = user_profile.organization
            except:
                pass
            
            # Parse captured_at
            captured_at = location_data.get('captured_at')
            if not captured_at:
                captured_at = timezone.now()
            
            # Save to history
            location_history = UserLocationHistory.objects.create(
                user=request.user,
                admin=admin,
                organization=organization,
                latitude=location_data['latitude'],
                longitude=location_data['longitude'],
                accuracy=location_data.get('accuracy'),
                altitude=location_data.get('altitude'),
                speed=location_data.get('speed'),
                heading=location_data.get('heading'),
                battery_percentage=location_data.get('battery_percentage'),
                is_charging=location_data.get('is_charging', False),
                is_moving=location_data.get('is_moving', False),
                address=location_data.get('address'),
                city=location_data.get('city'),
                state=location_data.get('state'),
                country=location_data.get('country'),
                pincode=location_data.get('pincode'),
                source=location_data.get('source', 'mobile'),
                device_id=location_data.get('device_id'),
                app_version=location_data.get('app_version'),
                captured_at=captured_at
            )
            
            # Update live location
            live_location, created = UserLiveLocation.objects.update_or_create(
                user=request.user,
                defaults={
                    'admin': admin,
                    'organization': organization,
                    'latitude': location_data['latitude'],
                    'longitude': location_data['longitude'],
                    'accuracy': location_data.get('accuracy'),
                    'altitude': location_data.get('altitude'),
                    'speed': location_data.get('speed'),
                    'heading': location_data.get('heading'),
                    'battery_percentage': location_data.get('battery_percentage'),
                    'is_charging': location_data.get('is_charging', False),
                    'is_moving': location_data.get('is_moving', False),
                    'address': location_data.get('address'),
                    'city': location_data.get('city'),
                    'state': location_data.get('state'),
                    'is_online': True,
                    'source': location_data.get('source', 'mobile'),
                    'device_id': location_data.get('device_id'),
                }
            )
            
            return Response({
                "status": status.HTTP_200_OK,
                "message": "Location updated successfully",
                "data": {
                    "history_id": str(location_history.id),
                    "live_location_id": str(live_location.id),
                    "timestamp": timezone.now().isoformat()
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
