"""
Advanced Visit Management Views
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.db.models import Q, Count, Sum
from django.utils import timezone
from datetime import datetime, date
from decimal import Decimal
import traceback

from .models import VisitAssignment, VisitTemplate, VisitChecklist, VisitReport
from .serializers import (
    VisitAssignmentSerializer, VisitTemplateSerializer,
    VisitChecklistSerializer, VisitReportSerializer
)
from AuthN.models import BaseUserModel, UserProfile
from utils.pagination_utils import CustomPagination


class VisitAssignmentAPIView(APIView):
    """Visit Assignment CRUD"""
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination
    
    def get(self, request, admin_id, pk=None):
        """Get visits"""
        try:
            admin = get_object_or_404(BaseUserModel, id=admin_id, role='admin')
            
            if pk:
                visit = get_object_or_404(VisitAssignment, id=pk, admin=admin)
                serializer = VisitAssignmentSerializer(visit)
                return Response({
                    "status": status.HTTP_200_OK,
                    "message": "Visit fetched successfully",
                    "data": serializer.data
                })
            else:
                queryset = VisitAssignment.objects.filter(admin=admin)
                
                # Filters
                status_filter = request.query_params.get('status')
                if status_filter:
                    queryset = queryset.filter(status=status_filter)
                
                user_id = request.query_params.get('user_id')
                if user_id:
                    queryset = queryset.filter(assigned_user_id=user_id)
                
                date_from = request.query_params.get('date_from')
                if date_from:
                    queryset = queryset.filter(meeting_date__gte=date_from)
                
                date_to = request.query_params.get('date_to')
                if date_to:
                    queryset = queryset.filter(meeting_date__lte=date_to)
                
                # Pagination
                paginator = self.pagination_class()
                paginated_qs = paginator.paginate_queryset(queryset, request)
                serializer = VisitAssignmentSerializer(paginated_qs, many=True)
                pagination_data = paginator.get_paginated_response(serializer.data)
                pagination_data["results"] = serializer.data
                pagination_data["message"] = "Visits fetched successfully"
                
                return Response(pagination_data)
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @transaction.atomic
    def post(self, request, admin_id):
        """Create visit"""
        try:
            admin = get_object_or_404(BaseUserModel, id=admin_id, role='admin')
            data = request.data.copy()
            data['admin'] = str(admin.id)
            data['organization'] = str(admin.own_admin_profile.organization.id)
            data['created_by'] = str(request.user.id)
            
            serializer = VisitAssignmentSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                return Response({
                    "status": status.HTTP_201_CREATED,
                    "message": "Visit created successfully",
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
    
    @transaction.atomic
    def put(self, request, admin_id, pk):
        """Update visit"""
        try:
            visit = get_object_or_404(VisitAssignment, id=pk, admin_id=admin_id)
            serializer = VisitAssignmentSerializer(visit, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({
                    "status": status.HTTP_200_OK,
                    "message": "Visit updated successfully",
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
    
    def delete(self, request, admin_id, pk):
        """Delete visit"""
        try:
            visit = get_object_or_404(VisitAssignment, id=pk, admin_id=admin_id)
            visit.delete()
            return Response({
                "status": status.HTTP_200_OK,
                "message": "Visit deleted successfully"
            })
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class VisitStartEndAPIView(APIView):
    """Start/End Visit Tracking"""
    permission_classes = [IsAuthenticated]
    
    @transaction.atomic
    def post(self, request, visit_id):
        """Start or end visit"""
        try:
            visit = get_object_or_404(VisitAssignment, id=visit_id)
            action = request.data.get('action')  # 'start' or 'end'
            latitude = request.data.get('latitude')
            longitude = request.data.get('longitude')
            
            if action == 'start':
                visit.status = 'in_progress'
                visit.actual_start_time = timezone.now()
                if latitude and longitude:
                    visit.start_latitude = Decimal(str(latitude))
                    visit.start_longitude = Decimal(str(longitude))
                visit.save()
                
                return Response({
                    "status": status.HTTP_200_OK,
                    "message": "Visit started successfully",
                    "data": VisitAssignmentSerializer(visit).data
                })
            
            elif action == 'end':
                visit.status = 'completed'
                visit.actual_end_time = timezone.now()
                if latitude and longitude:
                    visit.end_latitude = Decimal(str(latitude))
                    visit.end_longitude = Decimal(str(longitude))
                
                # Calculate duration
                if visit.actual_start_time:
                    duration = visit.actual_end_time - visit.actual_start_time
                    visit.duration_minutes = int(duration.total_seconds() / 60)
                
                visit.save()
                
                return Response({
                    "status": status.HTTP_200_OK,
                    "message": "Visit completed successfully",
                    "data": VisitAssignmentSerializer(visit).data
                })
            
            else:
                return Response({
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Invalid action. Use 'start' or 'end'"
                }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class VisitTemplateAPIView(APIView):
    """Visit Template CRUD"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, admin_id, pk=None):
        """Get templates"""
        try:
            admin = get_object_or_404(BaseUserModel, id=admin_id, role='admin')
            if pk:
                template = get_object_or_404(VisitTemplate, id=pk, admin=admin)
                serializer = VisitTemplateSerializer(template)
                return Response({
                    "status": status.HTTP_200_OK,
                    "message": "Template fetched successfully",
                    "data": serializer.data
                })
            else:
                templates = VisitTemplate.objects.filter(admin=admin, is_active=True)
                serializer = VisitTemplateSerializer(templates, many=True)
                return Response({
                    "status": status.HTTP_200_OK,
                    "message": "Templates fetched successfully",
                    "data": serializer.data
                })
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def post(self, request, admin_id):
        """Create template"""
        try:
            admin = get_object_or_404(BaseUserModel, id=admin_id, role='admin')
            data = request.data.copy()
            data['admin'] = str(admin.id)
            data['organization'] = str(admin.own_admin_profile.organization.id)
            
            serializer = VisitTemplateSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                return Response({
                    "status": status.HTTP_201_CREATED,
                    "message": "Template created successfully",
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


class VisitReportAPIView(APIView):
    """Visit Reports"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, admin_id):
        """Get visit reports"""
        try:
            admin = get_object_or_404(BaseUserModel, id=admin_id, role='admin')
            
            # Summary statistics
            visits = VisitAssignment.objects.filter(admin=admin)
            
            summary = {
                'total_visits': visits.count(),
                'scheduled': visits.filter(status='scheduled').count(),
                'in_progress': visits.filter(status='in_progress').count(),
                'completed': visits.filter(status='completed').count(),
                'cancelled': visits.filter(status='cancelled').count(),
            }
            
            return Response({
                "status": status.HTTP_200_OK,
                "message": "Reports fetched successfully",
                "data": summary
            })
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
