"""
Helpdesk Management Views
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.db.models import Q, Count
from django.utils import timezone
from datetime import datetime, date, timedelta
import uuid

from .models import TicketCategory, Ticket, TicketComment, TicketAssignmentRule, SLAPolicy
from .serializers import (
    TicketCategorySerializer, TicketSerializer, TicketCommentSerializer,
    TicketAssignmentRuleSerializer, SLAPolicySerializer
)
from AuthN.models import BaseUserModel
from utils.pagination_utils import CustomPagination


class TicketCategoryAPIView(APIView):
    """Ticket Category CRUD"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, org_id, pk=None):
        try:
            organization = get_object_or_404(BaseUserModel, id=org_id, role='organization')
            
            if pk:
                category = get_object_or_404(TicketCategory, id=pk, organization=organization)
                serializer = TicketCategorySerializer(category)
                return Response({
                    "status": status.HTTP_200_OK,
                    "message": "Category fetched successfully",
                    "data": serializer.data
                })
            else:
                categories = TicketCategory.objects.filter(organization=organization, is_active=True)
                serializer = TicketCategorySerializer(categories, many=True)
                return Response({
                    "status": status.HTTP_200_OK,
                    "message": "Categories fetched successfully",
                    "data": serializer.data
                })
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def post(self, request, org_id):
        try:
            organization = get_object_or_404(BaseUserModel, id=org_id, role='organization')
            admin_id = request.data.get('admin_id')
            admin = get_object_or_404(BaseUserModel, id=admin_id, role='admin') if admin_id else None
            
            data = request.data.copy()
            data['organization'] = str(organization.id)
            if admin:
                data['admin'] = str(admin.id)
            
            serializer = TicketCategorySerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                return Response({
                    "status": status.HTTP_201_CREATED,
                    "message": "Category created successfully",
                    "data": serializer.data
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


class TicketAPIView(APIView):
    """Ticket CRUD"""
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination
    
    def get(self, request, org_id, pk=None):
        try:
            organization = get_object_or_404(BaseUserModel, id=org_id, role='organization')
            
            if pk:
                ticket = get_object_or_404(Ticket, id=pk, organization=organization)
                serializer = TicketSerializer(ticket)
                return Response({
                    "status": status.HTTP_200_OK,
                    "message": "Ticket fetched successfully",
                    "data": serializer.data
                })
            else:
                tickets = Ticket.objects.filter(organization=organization)
                
                # Filters
                status_filter = request.query_params.get('status')
                priority_filter = request.query_params.get('priority')
                assigned_to = request.query_params.get('assigned_to')
                
                if status_filter:
                    tickets = tickets.filter(status=status_filter)
                if priority_filter:
                    tickets = tickets.filter(priority=priority_filter)
                if assigned_to:
                    tickets = tickets.filter(assigned_to_id=assigned_to)
                
                serializer = TicketSerializer(tickets.order_by('-created_at'), many=True)
                return Response({
                    "status": status.HTTP_200_OK,
                    "message": "Tickets fetched successfully",
                    "data": serializer.data
                })
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def post(self, request, org_id):
        try:
            organization = get_object_or_404(BaseUserModel, id=org_id, role='organization')
            admin_id = request.data.get('admin_id')
            admin = get_object_or_404(BaseUserModel, id=admin_id, role='admin') if admin_id else None
            
            data = request.data.copy()
            data['organization'] = str(organization.id)
            if admin:
                data['admin'] = str(admin.id)
            
            # Generate ticket number
            if 'ticket_number' not in data:
                data['ticket_number'] = f"TKT-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
            
            # Set SLA deadline if category has default SLA
            category_id = data.get('category')
            if category_id:
                category = TicketCategory.objects.filter(id=category_id).first()
                if category:
                    data['sla_hours'] = data.get('sla_hours', category.default_sla_hours)
                    if 'sla_deadline' not in data:
                        deadline = timezone.now() + timedelta(hours=data['sla_hours'])
                        data['sla_deadline'] = deadline
            
            serializer = TicketSerializer(data=data)
            if serializer.is_valid():
                ticket = serializer.save()
                return Response({
                    "status": status.HTTP_201_CREATED,
                    "message": "Ticket created successfully",
                    "data": TicketSerializer(ticket).data
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
    
    def put(self, request, org_id, pk):
        try:
            organization = get_object_or_404(BaseUserModel, id=org_id, role='organization')
            ticket = get_object_or_404(Ticket, id=pk, organization=organization)
            
            data = request.data.copy()
            serializer = TicketSerializer(ticket, data=data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({
                    "status": status.HTTP_200_OK,
                    "message": "Ticket updated successfully",
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


class TicketCommentAPIView(APIView):
    """Ticket Comment CRUD"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, ticket_id):
        try:
            ticket = get_object_or_404(Ticket, id=ticket_id)
            comments = TicketComment.objects.filter(ticket=ticket).order_by('created_at')
            serializer = TicketCommentSerializer(comments, many=True)
            return Response({
                "status": status.HTTP_200_OK,
                "message": "Comments fetched successfully",
                "data": serializer.data
            })
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def post(self, request, ticket_id):
        try:
            ticket = get_object_or_404(Ticket, id=ticket_id)
            user = request.user
            
            data = request.data.copy()
            data['ticket'] = str(ticket.id)
            data['user'] = str(user.id)
            
            serializer = TicketCommentSerializer(data=data)
            if serializer.is_valid():
                comment = serializer.save()
                
                # Update ticket first response time if this is first comment
                if not ticket.first_response_time:
                    ticket.first_response_time = timezone.now()
                    ticket.save()
                
                return Response({
                    "status": status.HTTP_201_CREATED,
                    "message": "Comment added successfully",
                    "data": TicketCommentSerializer(comment).data
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

