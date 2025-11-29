"""
Additional Utility APIs for Notification Management
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Q, Count
from django.utils import timezone
from datetime import datetime, date, timedelta

from .models import Notification, NotificationLog
from .serializers import NotificationSerializer
from AuthN.models import BaseUserModel, UserProfile
from utils.pagination_utils import CustomPagination


class NotificationDashboardAPIView(APIView):
    """Notification Dashboard Statistics"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, org_id):
        try:
            organization = get_object_or_404(BaseUserModel, id=org_id, role='organization')
            
            notifications = Notification.objects.filter(organization=organization)
            
            total = notifications.count()
            unread = notifications.filter(is_read=False).count()
            read = total - unread
            
            # Today's notifications
            today = date.today()
            today_notifications = notifications.filter(created_at__date=today).count()
            
            return Response({
                "status": status.HTTP_200_OK,
                "message": "Notification dashboard data fetched successfully",
                "data": {
                    "total": total,
                    "unread": unread,
                    "read": read,
                    "today": today_notifications
                }
            })
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": {}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserNotificationsAPIView(APIView):
    """Get notifications for a user"""
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination
    
    def get(self, request, user_id):
        try:
            user = get_object_or_404(BaseUserModel, id=user_id)
            
            notifications = Notification.objects.filter(user=user)
            
            is_read = request.query_params.get('is_read')
            notification_type = request.query_params.get('type')
            priority = request.query_params.get('priority')
            
            if is_read is not None:
                notifications = notifications.filter(is_read=is_read.lower() == 'true')
            if notification_type:
                notifications = notifications.filter(notification_type=notification_type)
            if priority:
                notifications = notifications.filter(priority=priority)
            
            notifications = notifications.order_by('-created_at')
            
            paginator = self.pagination_class()
            paginated_qs = paginator.paginate_queryset(notifications, request)
            
            serializer = NotificationSerializer(paginated_qs, many=True)
            pagination_data = paginator.get_paginated_response(serializer.data)
            
            # Unread count
            unread_count = Notification.objects.filter(user=user, is_read=False).count()
            pagination_data["unread_count"] = unread_count
            
            return Response({
                "status": status.HTTP_200_OK,
                "message": "Notifications fetched successfully",
                "data": pagination_data
            })
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def put(self, request, user_id, notification_id=None):
        """Mark notification as read"""
        try:
            user = get_object_or_404(BaseUserModel, id=user_id)
            
            if notification_id:
                # Mark single notification as read
                notification = get_object_or_404(Notification, id=notification_id, user=user)
                notification.is_read = True
                notification.read_at = timezone.now()
                notification.save()
                
                return Response({
                    "status": status.HTTP_200_OK,
                    "message": "Notification marked as read"
                })
            else:
                # Mark all as read
                updated = Notification.objects.filter(
                    user=user,
                    is_read=False
                ).update(
                    is_read=True,
                    read_at=timezone.now()
                )
                
                return Response({
                    "status": status.HTTP_200_OK,
                    "message": f"Marked {updated} notification(s) as read"
                })
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

