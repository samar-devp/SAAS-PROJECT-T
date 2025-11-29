"""
Additional Utility APIs for Helpdesk Management
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Q, Count
from django.utils import timezone
from datetime import datetime, date, timedelta

from .models import Ticket, TicketCategory
from .serializers import TicketSerializer
from AuthN.models import BaseUserModel, UserProfile
from utils.pagination_utils import CustomPagination


class HelpdeskDashboardAPIView(APIView):
    """Helpdesk Dashboard Statistics"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, org_id):
        try:
            organization = get_object_or_404(BaseUserModel, id=org_id, role='organization')
            
            tickets = Ticket.objects.filter(organization=organization)
            
            total = tickets.count()
            open_tickets = tickets.filter(status='open').count()
            in_progress = tickets.filter(status='in_progress').count()
            resolved = tickets.filter(status='resolved').count()
            closed = tickets.filter(status='closed').count()
            
            # SLA Status
            on_time = tickets.filter(sla_status='on_time').count()
            at_risk = tickets.filter(sla_status='at_risk').count()
            breached = tickets.filter(sla_status='breached').count()
            
            # Priority breakdown
            critical = tickets.filter(priority='critical').count()
            high = tickets.filter(priority='high').count()
            medium = tickets.filter(priority='medium').count()
            low = tickets.filter(priority='low').count()
            
            return Response({
                "status": status.HTTP_200_OK,
                "message": "Helpdesk dashboard data fetched successfully",
                "data": {
                    "total_tickets": total,
                    "open": open_tickets,
                    "in_progress": in_progress,
                    "resolved": resolved,
                    "closed": closed,
                    "sla": {
                        "on_time": on_time,
                        "at_risk": at_risk,
                        "breached": breached
                    },
                    "priority": {
                        "critical": critical,
                        "high": high,
                        "medium": medium,
                        "low": low
                    }
                }
            })
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": {}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AssignedTicketsAPIView(APIView):
    """Get tickets assigned to a user"""
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination
    
    def get(self, request, org_id, user_id):
        try:
            organization = get_object_or_404(BaseUserModel, id=org_id, role='organization')
            user = get_object_or_404(BaseUserModel, id=user_id)
            
            tickets = Ticket.objects.filter(
                organization=organization,
                assigned_to=user
            )
            
            status_filter = request.query_params.get('status')
            priority = request.query_params.get('priority')
            
            if status_filter:
                tickets = tickets.filter(status=status_filter)
            if priority:
                tickets = tickets.filter(priority=priority)
            
            tickets = tickets.order_by('-created_at')
            
            paginator = self.pagination_class()
            paginated_qs = paginator.paginate_queryset(tickets, request)
            
            serializer = TicketSerializer(paginated_qs, many=True)
            pagination_data = paginator.get_paginated_response(serializer.data)
            
            return Response({
                "status": status.HTTP_200_OK,
                "message": "Assigned tickets fetched successfully",
                "data": pagination_data
            })
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

