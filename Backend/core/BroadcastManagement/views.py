"""
Broadcast Management Views
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

from .models import Broadcast, BroadcastRecipient, BroadcastTemplate
from .serializers import (
    BroadcastSerializer, BroadcastRecipientSerializer, BroadcastTemplateSerializer
)
from AuthN.models import BaseUserModel, UserProfile
from utils.pagination_utils import CustomPagination


class BroadcastAPIView(APIView):
    """Broadcast CRUD"""
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination
    
    def get(self, request, org_id, pk=None):
        """Get broadcasts"""
        try:
            organization = get_object_or_404(BaseUserModel, id=org_id, role='organization')
            
            if pk:
                broadcast = get_object_or_404(Broadcast, id=pk, organization=organization)
                serializer = BroadcastSerializer(broadcast)
                return Response({
                    "status": status.HTTP_200_OK,
                    "message": "Broadcast fetched successfully",
                    "data": serializer.data
                })
            else:
                queryset = Broadcast.objects.filter(organization=organization)
                
                # Filters
                status_filter = request.query_params.get('status')
                if status_filter:
                    queryset = queryset.filter(status=status_filter)
                
                broadcast_type = request.query_params.get('type')
                if broadcast_type:
                    queryset = queryset.filter(broadcast_type=broadcast_type)
                
                # Pagination
                paginator = self.pagination_class()
                paginated_qs = paginator.paginate_queryset(queryset, request)
                serializer = BroadcastSerializer(paginated_qs, many=True)
                pagination_data = paginator.get_paginated_response(serializer.data)
                pagination_data["results"] = serializer.data
                pagination_data["message"] = "Broadcasts fetched successfully"
                
                return Response(pagination_data)
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @transaction.atomic
    def post(self, request, org_id):
        """Create broadcast"""
        try:
            organization = get_object_or_404(BaseUserModel, id=org_id, role='organization')
            admin = get_object_or_404(BaseUserModel, id=request.data.get('admin_id'), role='admin')
            
            data = request.data.copy()
            data['organization'] = str(organization.id)
            data['admin'] = str(admin.id)
            data['created_by'] = str(request.user.id)
            
            serializer = BroadcastSerializer(data=data)
            if serializer.is_valid():
                broadcast = serializer.save()
                
                # Determine recipients based on target_audience
                recipients = []
                target_audience = data.get('target_audience', 'all')
                
                if target_audience == 'all':
                    user_profiles = UserProfile.objects.filter(organization=organization)
                    recipients = [profile.user for profile in user_profiles]
                elif target_audience == 'individual':
                    target_user_ids = request.data.get('target_user_ids', [])
                    recipients = BaseUserModel.objects.filter(id__in=target_user_ids, role='user')
                # Add more targeting logic as needed
                
                # Create recipient records
                for recipient in recipients:
                    BroadcastRecipient.objects.create(
                        broadcast=broadcast,
                        user=recipient
                    )
                
                broadcast.total_recipients = len(recipients)
                broadcast.save()
                
                return Response({
                    "status": status.HTTP_201_CREATED,
                    "message": "Broadcast created successfully",
                    "data": BroadcastSerializer(broadcast).data
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
    def put(self, request, org_id, pk):
        """Update broadcast"""
        try:
            broadcast = get_object_or_404(Broadcast, id=pk, organization_id=org_id)
            
            # If publishing, set published_at
            if 'status' in request.data and request.data['status'] == 'published' and broadcast.status != 'published':
                request.data['published_at'] = timezone.now()
            
            serializer = BroadcastSerializer(broadcast, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({
                    "status": status.HTTP_200_OK,
                    "message": "Broadcast updated successfully",
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


class BroadcastRecipientAPIView(APIView):
    """Broadcast Recipient Management"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, broadcast_id):
        """Get recipients"""
        try:
            broadcast = get_object_or_404(Broadcast, id=broadcast_id)
            recipients = BroadcastRecipient.objects.filter(broadcast=broadcast)
            serializer = BroadcastRecipientSerializer(recipients, many=True)
            return Response({
                "status": status.HTTP_200_OK,
                "message": "Recipients fetched successfully",
                "data": serializer.data
            })
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @transaction.atomic
    def post(self, request, broadcast_id):
        """Mark as read/acknowledge"""
        try:
            broadcast = get_object_or_404(Broadcast, id=broadcast_id)
            user = request.user
            action = request.data.get('action')  # 'read' or 'acknowledge'
            
            recipient, created = BroadcastRecipient.objects.get_or_create(
                broadcast=broadcast,
                user=user
            )
            
            if action == 'read':
                recipient.is_read = True
                recipient.read_at = timezone.now()
                recipient.save()
                
                # Update broadcast read count
                broadcast.read_count = BroadcastRecipient.objects.filter(
                    broadcast=broadcast, is_read=True
                ).count()
                broadcast.save()
                
                return Response({
                    "status": status.HTTP_200_OK,
                    "message": "Marked as read",
                    "data": BroadcastRecipientSerializer(recipient).data
                })
            
            elif action == 'acknowledge':
                recipient.is_acknowledged = True
                recipient.acknowledged_at = timezone.now()
                recipient.save()
                
                # Update broadcast acknowledged count
                broadcast.acknowledged_count = BroadcastRecipient.objects.filter(
                    broadcast=broadcast, is_acknowledged=True
                ).count()
                broadcast.save()
                
                return Response({
                    "status": status.HTTP_200_OK,
                    "message": "Acknowledged",
                    "data": BroadcastRecipientSerializer(recipient).data
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

