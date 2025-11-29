"""
Additional Utility APIs for Broadcast Management
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Q, Count
from django.utils import timezone
from datetime import datetime, date

from .models import Broadcast, BroadcastRecipient
from .serializers import BroadcastSerializer
from AuthN.models import BaseUserModel, UserProfile
from utils.pagination_utils import CustomPagination


class BroadcastDashboardAPIView(APIView):
    """Broadcast Dashboard Statistics"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, org_id):
        try:
            organization = get_object_or_404(BaseUserModel, id=org_id, role='organization')
            
            broadcasts = Broadcast.objects.filter(organization=organization)
            
            total_broadcasts = broadcasts.count()
            scheduled = broadcasts.filter(status='scheduled').count()
            sent = broadcasts.filter(status='sent').count()
            cancelled = broadcasts.filter(status='cancelled').count()
            
            # Recipients stats
            total_recipients = BroadcastRecipient.objects.filter(
                broadcast__organization=organization
            ).count()
            acknowledged = BroadcastRecipient.objects.filter(
                broadcast__organization=organization,
                acknowledged=True
            ).count()
            
            return Response({
                "status": status.HTTP_200_OK,
                "message": "Broadcast dashboard data fetched successfully",
                "data": {
                    "total_broadcasts": total_broadcasts,
                    "scheduled": scheduled,
                    "sent": sent,
                    "cancelled": cancelled,
                    "total_recipients": total_recipients,
                    "acknowledged": acknowledged,
                    "acknowledgment_rate": round((acknowledged / total_recipients * 100) if total_recipients > 0 else 0, 2)
                }
            })
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": {}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class BroadcastListAPIView(APIView):
    """Get broadcasts list"""
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination
    
    def get(self, request, org_id):
        try:
            organization = get_object_or_404(BaseUserModel, id=org_id, role='organization')
            
            broadcasts = Broadcast.objects.filter(organization=organization)
            
            status_filter = request.query_params.get('status')
            channel = request.query_params.get('channel')
            
            if status_filter:
                broadcasts = broadcasts.filter(status=status_filter)
            if channel:
                broadcasts = broadcasts.filter(channels__contains=[channel])
            
            broadcasts = broadcasts.order_by('-scheduled_at', '-created_at')
            
            paginator = self.pagination_class()
            paginated_qs = paginator.paginate_queryset(broadcasts, request)
            
            serializer = BroadcastSerializer(paginated_qs, many=True)
            pagination_data = paginator.get_paginated_response(serializer.data)
            
            return Response({
                "status": status.HTTP_200_OK,
                "message": "Broadcasts fetched successfully",
                "data": pagination_data
            })
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

