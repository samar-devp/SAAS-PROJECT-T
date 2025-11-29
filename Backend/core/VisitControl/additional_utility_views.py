"""
Additional Utility APIs for Visit Management
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Q, Count
from django.utils import timezone
from datetime import datetime, date

from .models import VisitAssignment, VisitTemplate
from .serializers import VisitAssignmentSerializer, VisitTemplateSerializer
from AuthN.models import BaseUserModel, UserProfile
from utils.pagination_utils import CustomPagination


class VisitDashboardAPIView(APIView):
    """Visit Dashboard Statistics"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, org_id):
        try:
            organization = get_object_or_404(BaseUserModel, id=org_id, role='organization')
            
            user_profiles = UserProfile.objects.filter(organization=organization)
            employee_ids = [p.user.id for p in user_profiles]
            
            visits = VisitAssignment.objects.filter(visitor_id__in=employee_ids)
            
            total_visits = visits.count()
            scheduled = visits.filter(status='scheduled').count()
            in_progress = visits.filter(status='in_progress').count()
            completed = visits.filter(status='completed').count()
            cancelled = visits.filter(status='cancelled').count()
            
            return Response({
                "status": status.HTTP_200_OK,
                "message": "Visit dashboard data fetched successfully",
                "data": {
                    "total_visits": total_visits,
                    "scheduled": scheduled,
                    "in_progress": in_progress,
                    "completed": completed,
                    "cancelled": cancelled
                }
            })
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": {}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class EmployeeVisitListAPIView(APIView):
    """Get visits for an employee"""
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination
    
    def get(self, request, org_id, employee_id):
        try:
            organization = get_object_or_404(BaseUserModel, id=org_id, role='organization')
            employee = get_object_or_404(BaseUserModel, id=employee_id, role='user')
            
            visits = VisitAssignment.objects.filter(visitor=employee)
            
            status_filter = request.query_params.get('status')
            if status_filter:
                visits = visits.filter(status=status_filter)
            
            visits = visits.order_by('-scheduled_date')
            
            paginator = self.pagination_class()
            paginated_qs = paginator.paginate_queryset(visits, request)
            
            serializer = VisitAssignmentSerializer(paginated_qs, many=True)
            pagination_data = paginator.get_paginated_response(serializer.data)
            
            return Response({
                "status": status.HTTP_200_OK,
                "message": "Visits fetched successfully",
                "data": pagination_data
            })
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

