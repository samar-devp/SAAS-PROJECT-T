"""
Visit Management Views
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from decimal import Decimal

from .models import Visit
from .serializers import (
    VisitSerializer, VisitCreateSerializer,
    VisitCheckInSerializer, VisitCheckOutSerializer
)
from AuthN.models import BaseUserModel
from utils.pagination_utils import CustomPagination


class VisitAPIView(APIView):
    """
    Visit CRUD Operations
    - Admin can create visits and assign them to employees
    - Employees can create their own visits
    - Admin can see all visits
    - Employees can only see their assigned or self-created visits
    """
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination
    
    def get(self, request, admin_id, user_id=None, pk=None):
        """Get visits - filtered by role"""
        try:
            admin = get_object_or_404(BaseUserModel, id=admin_id, role='admin')
            user = request.user
            
            if pk:
                # Get specific visit
                visit = get_object_or_404(Visit, id=pk, admin=admin)
                
                # Check access permission
                if user.role == 'user' and visit.assigned_employee != user and visit.created_by != user:
                    return Response({
                        "status": status.HTTP_403_FORBIDDEN,
                        "message": "You don't have permission to view this visit",
                        "data": None
                    }, status=status.HTTP_403_FORBIDDEN)
                
                serializer = VisitSerializer(visit)
                return Response({
                    "status": status.HTTP_200_OK,
                    "message": "Visit fetched successfully",
                    "data": serializer.data
                })
            else:
                # Get list of visits
                if user.role == 'admin':
                    # Admin can see all visits
                    queryset = Visit.objects.filter(admin=admin)
                    # Filter by user_id if provided
                    if user_id:
                        queryset = queryset.filter(assigned_employee_id=user_id)
                elif user.role == 'user':
                    # Employees can only see their assigned or self-created visits
                    queryset = Visit.objects.filter(
                        admin=admin
                    ).filter(
                        Q(assigned_employee=user) | Q(created_by=user)
                    )
                else:
                    queryset = Visit.objects.none()
                
                # Apply filters
                status_filter = request.query_params.get('status')
                if status_filter:
                    queryset = queryset.filter(status=status_filter)
                
                date_from = request.query_params.get('date_from')
                if date_from:
                    queryset = queryset.filter(schedule_date__gte=date_from)
                
                date_to = request.query_params.get('date_to')
                if date_to:
                    queryset = queryset.filter(schedule_date__lte=date_to)
                
                # Pagination
                paginator = self.pagination_class()
                paginated_qs = paginator.paginate_queryset(queryset, request)
                serializer = VisitSerializer(paginated_qs, many=True)
                pagination_data = paginator.get_paginated_response(serializer.data)
                
                return Response({
                    "status": status.HTTP_200_OK,
                    "message": "Visits fetched successfully",
                    "data": {
                        "results": serializer.data,
                        "count": pagination_data.get('total_objects', len(serializer.data)),
                        "next": pagination_data.get('next_page_number'),
                        "previous": pagination_data.get('previous_page_number')
                    }
                })
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @transaction.atomic
    def post(self, request, admin_id, user_id=None):
        """Create visit - Admin or Employee can create"""
        try:
            admin = get_object_or_404(BaseUserModel, id=admin_id, role='admin')
            user = request.user
            
            data = request.data.copy()
            data['admin'] = str(admin.id)
            data['created_by'] = str(user.id)
            
            # If employee is creating, they can assign to themselves or leave it to admin
            if user.role == 'user':
                # If assigned_employee is not provided, assign to the creator
                if 'assigned_employee' not in data or not data['assigned_employee']:
                    data['assigned_employee'] = str(user.id)
                # Employees can only assign to themselves
                elif data['assigned_employee'] != str(user.id):
                    return Response({
                        "status": status.HTTP_403_FORBIDDEN,
                        "message": "Employees can only create visits for themselves",
                        "data": None
                    }, status=status.HTTP_403_FORBIDDEN)
            
            # If user_id is provided in URL and user is admin, use it
            if user_id and user.role == 'admin':
                data['assigned_employee'] = str(user_id)
            
            serializer = VisitCreateSerializer(data=data)
            if serializer.is_valid():
                visit = serializer.save(
                    admin=admin,
                    created_by=user
                )
                
                response_serializer = VisitSerializer(visit)
                return Response({
                    "status": status.HTTP_201_CREATED,
                    "message": "Visit created successfully",
                    "data": response_serializer.data
                }, status=status.HTTP_201_CREATED)
            
            return Response({
                "status": status.HTTP_400_BAD_REQUEST,
                "message": "Validation error",
                "data": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @transaction.atomic
    def put(self, request, admin_id, user_id=None, pk=None):
        """Update visit"""
        try:
            if not pk:
                return Response({
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Visit ID is required",
                    "data": None
                }, status=status.HTTP_400_BAD_REQUEST)
            
            visit = get_object_or_404(Visit, id=pk, admin_id=admin_id)
            user = request.user
            
            # Check permission - only admin or creator can update
            if user.role == 'user' and visit.created_by != user:
                return Response({
                    "status": status.HTTP_403_FORBIDDEN,
                    "message": "You don't have permission to update this visit",
                    "data": None
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Don't allow updating status directly through this endpoint
            data = request.data.copy()
            if 'status' in data:
                data.pop('status')
            
            serializer = VisitCreateSerializer(visit, data=data, partial=True)
            if serializer.is_valid():
                serializer.save()
                
                response_serializer = VisitSerializer(visit)
                return Response({
                    "status": status.HTTP_200_OK,
                    "message": "Visit updated successfully",
                    "data": response_serializer.data
                })
            
            return Response({
                "status": status.HTTP_400_BAD_REQUEST,
                "message": "Validation error",
                "data": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def delete(self, request, admin_id, user_id=None, pk=None):
        """Delete visit - Only admin or creator can delete"""
        try:
            if not pk:
                return Response({
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Visit ID is required",
                    "data": None
                }, status=status.HTTP_400_BAD_REQUEST)
            
            visit = get_object_or_404(Visit, id=pk, admin_id=admin_id)
            user = request.user
            
            # Check permission
            if user.role == 'user' and visit.created_by != user:
                return Response({
                    "status": status.HTTP_403_FORBIDDEN,
                    "message": "You don't have permission to delete this visit",
                    "data": None
                }, status=status.HTTP_403_FORBIDDEN)
            
            visit.delete()
            return Response({
                "status": status.HTTP_200_OK,
                "message": "Visit deleted successfully",
                "data": None
            })
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class VisitCheckInAPIView(APIView):
    """
    Check-In Endpoint
    - Employee must send GPS coordinates (latitude, longitude)
    - Optional note
    - Updates visit status to 'in_progress'
    - Only assigned employee (or creator if self-visit) can check-in
    """
    permission_classes = [IsAuthenticated]
    
    @transaction.atomic
    def post(self, request, admin_id, user_id, visit_id):
        """Perform check-in"""
        try:
            visit = get_object_or_404(Visit, id=visit_id, admin_id=admin_id)
            user = request.user
            
            # Check permission
            if not visit.can_perform_check_in_out(user):
                return Response({
                    "status": status.HTTP_403_FORBIDDEN,
                    "message": "You don't have permission to check-in for this visit",
                    "data": None
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Check if already checked in
            if visit.status == 'in_progress':
                return Response({
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Visit is already in progress. Please check-out first.",
                    "data": None
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if visit.status == 'completed':
                return Response({
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Cannot check-in to a completed visit",
                    "data": None
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Validate check-in data
            serializer = VisitCheckInSerializer(data=request.data)
            if not serializer.is_valid():
                return Response({
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Validation error",
                    "data": serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            validated_data = serializer.validated_data
            latitude = validated_data['latitude']
            longitude = validated_data['longitude']
            note = validated_data.get('note', '')
            
            # Update visit
            check_in_time = timezone.now()
            visit.status = 'in_progress'
            visit.check_in_timestamp = check_in_time
            visit.check_in_latitude = Decimal(str(latitude))
            visit.check_in_longitude = Decimal(str(longitude))
            visit.check_in_note = note
            visit.save()
            
            response_serializer = VisitSerializer(visit)
            return Response({
                "status": status.HTTP_200_OK,
                "message": "Check-in successful",
                "data": response_serializer.data
            })
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class VisitCheckOutAPIView(APIView):
    """
    Check-Out Endpoint
    - Employee must send GPS coordinates (latitude, longitude)
    - Optional note
    - Updates visit status to 'completed'
    - Only assigned employee (or creator if self-visit) can check-out
    """
    permission_classes = [IsAuthenticated]
    
    @transaction.atomic
    def post(self, request, admin_id, user_id, visit_id):
        """Perform check-out"""
        try:
            visit = get_object_or_404(Visit, id=visit_id, admin_id=admin_id)
            user = request.user
            
            # Check permission
            if not visit.can_perform_check_in_out(user):
                return Response({
                    "status": status.HTTP_403_FORBIDDEN,
                    "message": "You don't have permission to check-out for this visit",
                    "data": None
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Check if visit is in progress
            if visit.status != 'in_progress':
                return Response({
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Visit must be in progress before checking out. Please check-in first.",
                    "data": None
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Validate check-out data
            serializer = VisitCheckOutSerializer(data=request.data)
            if not serializer.is_valid():
                return Response({
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Validation error",
                    "data": serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            validated_data = serializer.validated_data
            latitude = validated_data['latitude']
            longitude = validated_data['longitude']
            note = validated_data.get('note', '')
            
            # Update visit
            check_out_time = timezone.now()
            visit.status = 'completed'
            visit.check_out_timestamp = check_out_time
            visit.check_out_latitude = Decimal(str(latitude))
            visit.check_out_longitude = Decimal(str(longitude))
            visit.check_out_note = note
            visit.save()
            
            response_serializer = VisitSerializer(visit)
            return Response({
                "status": status.HTTP_200_OK,
                "message": "Check-out successful",
                "data": response_serializer.data
            })
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class VisitStatsAPIView(APIView):
    """
    Get visit statistics
    - Admin can see all statistics
    - Employees can see their own statistics
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, admin_id, user_id=None):
        """Get visit statistics"""
        try:
            admin = get_object_or_404(BaseUserModel, id=admin_id, role='admin')
            user = request.user
            
            # Build queryset based on role
            if user.role == 'admin':
                visits = Visit.objects.filter(admin=admin)
                if user_id:
                    visits = visits.filter(assigned_employee_id=user_id)
            elif user.role == 'user':
                visits = Visit.objects.filter(
                    admin=admin
                ).filter(
                    Q(assigned_employee=user) | Q(created_by=user)
                )
            else:
                visits = Visit.objects.none()
            
            stats = {
                'total_visits': visits.count(),
                'pending': visits.filter(status='pending').count(),
                'in_progress': visits.filter(status='in_progress').count(),
                'completed': visits.filter(status='completed').count(),
                'cancelled': visits.filter(status='cancelled').count(),
            }
            
            return Response({
                "status": status.HTTP_200_OK,
                "message": "Statistics fetched successfully",
                "data": stats
            })
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
