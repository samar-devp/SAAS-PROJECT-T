"""
Additional Utility APIs for Notes Management
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Q, Count
from django.utils import timezone
from datetime import datetime, date

from .models import Note, NoteCategory
from .serializers import NoteSerializer, NoteCategorySerializer
from AuthN.models import BaseUserModel, UserProfile
from utils.pagination_utils import CustomPagination


class NotesDashboardAPIView(APIView):
    """Notes Dashboard Statistics"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, org_id):
        try:
            organization = get_object_or_404(BaseUserModel, id=org_id, role='organization')
            
            user_profiles = UserProfile.objects.filter(organization=organization)
            employee_ids = [p.user.id for p in user_profiles]
            
            notes = Note.objects.filter(created_by_id__in=employee_ids)
            
            total_notes = notes.count()
            shared_notes = notes.filter(is_shared=True).count()
            private_notes = total_notes - shared_notes
            
            categories_count = NoteCategory.objects.filter(organization=organization).count()
            
            return Response({
                "status": status.HTTP_200_OK,
                "message": "Notes dashboard data fetched successfully",
                "data": {
                    "total_notes": total_notes,
                    "shared_notes": shared_notes,
                    "private_notes": private_notes,
                    "categories": categories_count
                }
            })
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": {}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class EmployeeNotesListAPIView(APIView):
    """Get notes for an employee"""
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination
    
    def get(self, request, org_id, employee_id):
        try:
            organization = get_object_or_404(BaseUserModel, id=org_id, role='organization')
            employee = get_object_or_404(BaseUserModel, id=employee_id, role='user')
            
            notes = Note.objects.filter(created_by=employee)
            
            category_id = request.query_params.get('category_id')
            is_shared = request.query_params.get('is_shared')
            
            if category_id:
                notes = notes.filter(category_id=category_id)
            if is_shared is not None:
                notes = notes.filter(is_shared=is_shared.lower() == 'true')
            
            notes = notes.order_by('-created_at')
            
            paginator = self.pagination_class()
            paginated_qs = paginator.paginate_queryset(notes, request)
            
            serializer = NoteSerializer(paginated_qs, many=True)
            pagination_data = paginator.get_paginated_response(serializer.data)
            
            return Response({
                "status": status.HTTP_200_OK,
                "message": "Notes fetched successfully",
                "data": pagination_data
            })
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

