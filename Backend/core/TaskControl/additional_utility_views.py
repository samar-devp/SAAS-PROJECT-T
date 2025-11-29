"""
Additional Utility APIs for Task Management
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Q, Count, Sum
from django.utils import timezone
from datetime import datetime, date

from .models import Project, Task, TaskComment, TaskTimeLog
from .serializers import ProjectSerializer, TaskSerializer
from AuthN.models import BaseUserModel, UserProfile
from utils.pagination_utils import CustomPagination


class TaskDashboardAPIView(APIView):
    """Task Dashboard Statistics"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, org_id):
        try:
            organization = get_object_or_404(BaseUserModel, id=org_id, role='organization')
            
            user_profiles = UserProfile.objects.filter(organization=organization)
            employee_ids = [p.user.id for p in user_profiles]
            
            tasks = Task.objects.filter(assigned_to_id__in=employee_ids)
            
            total_tasks = tasks.count()
            pending = tasks.filter(status='pending').count()
            in_progress = tasks.filter(status='in_progress').count()
            completed = tasks.filter(status='completed').count()
            overdue = tasks.filter(
                due_date__lt=date.today(),
                status__in=['pending', 'in_progress']
            ).count()
            
            return Response({
                "status": status.HTTP_200_OK,
                "message": "Task dashboard data fetched successfully",
                "data": {
                    "total_tasks": total_tasks,
                    "pending": pending,
                    "in_progress": in_progress,
                    "completed": completed,
                    "overdue": overdue,
                    "completion_rate": round((completed / total_tasks * 100) if total_tasks > 0 else 0, 2)
                }
            })
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": {}
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class EmployeeTaskListAPIView(APIView):
    """Get tasks assigned to an employee"""
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination
    
    def get(self, request, org_id, employee_id):
        try:
            organization = get_object_or_404(BaseUserModel, id=org_id, role='organization')
            employee = get_object_or_404(BaseUserModel, id=employee_id, role='user')
            
            tasks = Task.objects.filter(assigned_to=employee)
            
            status_filter = request.query_params.get('status')
            priority = request.query_params.get('priority')
            project_id = request.query_params.get('project_id')
            
            if status_filter:
                tasks = tasks.filter(status=status_filter)
            if priority:
                tasks = tasks.filter(priority=priority)
            if project_id:
                tasks = tasks.filter(project_id=project_id)
            
            tasks = tasks.order_by('-created_at')
            
            paginator = self.pagination_class()
            paginated_qs = paginator.paginate_queryset(tasks, request)
            
            serializer = TaskSerializer(paginated_qs, many=True)
            pagination_data = paginator.get_paginated_response(serializer.data)
            
            return Response({
                "status": status.HTTP_200_OK,
                "message": "Tasks fetched successfully",
                "data": pagination_data
            })
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ProjectListAPIView(APIView):
    """Get projects list"""
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination
    
    def get(self, request, org_id):
        try:
            organization = get_object_or_404(BaseUserModel, id=org_id, role='organization')
            
            projects = Project.objects.filter(organization=organization)
            
            status_filter = request.query_params.get('status')
            if status_filter:
                projects = projects.filter(status=status_filter)
            
            projects = projects.order_by('-created_at')
            
            paginator = self.pagination_class()
            paginated_qs = paginator.paginate_queryset(projects, request)
            
            serializer = ProjectSerializer(paginated_qs, many=True)
            pagination_data = paginator.get_paginated_response(serializer.data)
            
            return Response({
                "status": status.HTTP_200_OK,
                "message": "Projects fetched successfully",
                "data": pagination_data
            })
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

