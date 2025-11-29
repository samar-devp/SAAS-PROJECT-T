"""
Notification Management Views
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.db.models import Q, Count
from django.utils import timezone
from datetime import datetime, date
import traceback

from .models import Notification, NotificationPreference, NotificationTemplate, NotificationLog
from .serializers import (
    NotificationSerializer, NotificationPreferenceSerializer,
    NotificationTemplateSerializer, NotificationLogSerializer
)
from AuthN.models import BaseUserModel, UserProfile
from utils.pagination_utils import CustomPagination


class NotificationAPIView(APIView):
    """Notification CRUD"""
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination
    
    def get(self, request, user_id, pk=None):
        """Get notifications"""
        try:
            user = get_object_or_404(BaseUserModel, id=user_id, role='user')
            
            if pk:
                notification = get_object_or_404(Notification, id=pk, user=user)
                serializer = NotificationSerializer(notification)
                return Response({
                    "status": status.HTTP_200_OK,
                    "message": "Notification fetched successfully",
                    "data": serializer.data
                })
            else:
                queryset = Notification.objects.filter(user=user, is_archived=False)
                
                # Filters
                is_read = request.query_params.get('is_read')
                if is_read == 'true':
                    queryset = queryset.filter(is_read=True)
                elif is_read == 'false':
                    queryset = queryset.filter(is_read=False)
                
                notification_type = request.query_params.get('type')
                if notification_type:
                    queryset = queryset.filter(notification_type=notification_type)
                
                # Pagination
                paginator = self.pagination_class()
                paginated_qs = paginator.paginate_queryset(queryset, request)
                serializer = NotificationSerializer(paginated_qs, many=True)
                pagination_data = paginator.get_paginated_response(serializer.data)
                pagination_data["results"] = serializer.data
                
                # Unread count
                unread_count = Notification.objects.filter(user=user, is_read=False, is_archived=False).count()
                pagination_data["unread_count"] = unread_count
                pagination_data["message"] = "Notifications fetched successfully"
                
                return Response(pagination_data)
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @transaction.atomic
    def post(self, request, user_id):
        """Create notification"""
        try:
            user = get_object_or_404(BaseUserModel, id=user_id, role='user')
            user_profile = user.own_user_profile
            
            data = request.data.copy()
            data['user'] = str(user.id)
            data['admin'] = str(user_profile.admin.id)
            data['organization'] = str(user_profile.organization.id)
            
            serializer = NotificationSerializer(data=data)
            if serializer.is_valid():
                notification = serializer.save()
                
                # Create delivery logs based on sent_via
                sent_via = data.get('sent_via', ['in_app'])
                for channel in sent_via:
                    NotificationLog.objects.create(
                        notification=notification,
                        channel=channel,
                        status='sent'
                    )
                
                return Response({
                    "status": status.HTTP_201_CREATED,
                    "message": "Notification created successfully",
                    "data": NotificationSerializer(notification).data
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
    
    @transaction.atomic
    def put(self, request, user_id, pk):
        """Update notification (mark as read/archive)"""
        try:
            notification = get_object_or_404(Notification, id=pk, user_id=user_id)
            action = request.data.get('action')  # 'read', 'unread', 'archive', 'unarchive'
            
            if action == 'read':
                notification.is_read = True
                notification.read_at = timezone.now()
                notification.save()
                
                return Response({
                    "status": status.HTTP_200_OK,
                    "message": "Notification marked as read",
                    "data": NotificationSerializer(notification).data
                })
            
            elif action == 'unread':
                notification.is_read = False
                notification.read_at = None
                notification.save()
                
                return Response({
                    "status": status.HTTP_200_OK,
                    "message": "Notification marked as unread",
                    "data": NotificationSerializer(notification).data
                })
            
            elif action == 'archive':
                notification.is_archived = True
                notification.archived_at = timezone.now()
                notification.save()
                
                return Response({
                    "status": status.HTTP_200_OK,
                    "message": "Notification archived",
                    "data": NotificationSerializer(notification).data
                })
            
            elif action == 'unarchive':
                notification.is_archived = False
                notification.archived_at = None
                notification.save()
                
                return Response({
                    "status": status.HTTP_200_OK,
                    "message": "Notification unarchived",
                    "data": NotificationSerializer(notification).data
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


class NotificationPreferenceAPIView(APIView):
    """Notification Preferences"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, user_id):
        """Get preferences"""
        try:
            user = get_object_or_404(BaseUserModel, id=user_id, role='user')
            preference, created = NotificationPreference.objects.get_or_create(
                user=user,
                defaults={'organization': user.own_user_profile.organization}
            )
            serializer = NotificationPreferenceSerializer(preference)
            return Response({
                "status": status.HTTP_200_OK,
                "message": "Preferences fetched successfully",
                "data": serializer.data
            })
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def put(self, request, user_id):
        """Update preferences"""
        try:
            user = get_object_or_404(BaseUserModel, id=user_id, role='user')
            preference, created = NotificationPreference.objects.get_or_create(
                user=user,
                defaults={'organization': user.own_user_profile.organization}
            )
            serializer = NotificationPreferenceSerializer(preference, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({
                    "status": status.HTTP_200_OK,
                    "message": "Preferences updated successfully",
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


class NotificationMarkAllReadAPIView(APIView):
    """Mark all notifications as read"""
    permission_classes = [IsAuthenticated]
    
    @transaction.atomic
    def post(self, request, user_id):
        """Mark all as read"""
        try:
            user = get_object_or_404(BaseUserModel, id=user_id, role='user')
            updated = Notification.objects.filter(
                user=user,
                is_read=False,
                is_archived=False
            ).update(
                is_read=True,
                read_at=timezone.now()
            )
            
            return Response({
                "status": status.HTTP_200_OK,
                "message": f"{updated} notifications marked as read",
                "updated_count": updated
            })
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
