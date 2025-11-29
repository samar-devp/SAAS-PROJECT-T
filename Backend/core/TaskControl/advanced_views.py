"""
Advanced Task Management Views
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.db.models import Q, Count, Sum, Avg
from django.utils import timezone
from datetime import datetime, date
from decimal import Decimal
import traceback

from .models import Project, Task, TaskComment, TaskTimeLog, TaskAttachment
from .serializers import (
    ProjectSerializer, TaskSerializer, TaskCommentSerializer,
    TaskTimeLogSerializer, TaskAttachmentSerializer
)
from AuthN.models import BaseUserModel, UserProfile
from utils.pagination_utils import CustomPagination


class ProjectAPIView(APIView):
    """Project CRUD"""
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination
    
    def get(self, request, admin_id, pk=None):
        """Get projects"""
        try:
            admin = get_object_or_404(BaseUserModel, id=admin_id, role='admin')
            
            if pk:
                project = get_object_or_404(Project, id=pk, admin=admin)
                serializer = ProjectSerializer(project)
                return Response({
                    "status": status.HTTP_200_OK,
                    "message": "Project fetched successfully",
                    "data": serializer.data
                })
            else:
                queryset = Project.objects.filter(admin=admin, is_active=True)
                
                # Filters
                status_filter = request.query_params.get('status')
                if status_filter:
                    queryset = queryset.filter(status=status_filter)
                
                # Pagination
                paginator = self.pagination_class()
                paginated_qs = paginator.paginate_queryset(queryset, request)
                serializer = ProjectSerializer(paginated_qs, many=True)
                pagination_data = paginator.get_paginated_response(serializer.data)
                pagination_data["results"] = serializer.data
                pagination_data["message"] = "Projects fetched successfully"
                
                return Response(pagination_data)
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @transaction.atomic
    def post(self, request, admin_id):
        """Create project"""
        try:
            admin = get_object_or_404(BaseUserModel, id=admin_id, role='admin')
            data = request.data.copy()
            data['admin'] = str(admin.id)
            data['organization'] = str(admin.own_admin_profile.organization.id)
            
            serializer = ProjectSerializer(data=data)
            if serializer.is_valid():
                project = serializer.save()
                
                # Add team members if provided
                team_member_ids = request.data.get('team_member_ids', [])
                if team_member_ids:
                    team_members = BaseUserModel.objects.filter(id__in=team_member_ids, role='user')
                    project.team_members.set(team_members)
                
                return Response({
                    "status": status.HTTP_201_CREATED,
                    "message": "Project created successfully",
                    "data": ProjectSerializer(project).data
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
        """Update project"""
        try:
            project = get_object_or_404(Project, id=pk, admin_id=admin_id)
            serializer = ProjectSerializer(project, data=request.data, partial=True)
            if serializer.is_valid():
                project = serializer.save()
                
                # Update team members if provided
                if 'team_member_ids' in request.data:
                    team_member_ids = request.data.get('team_member_ids', [])
                    team_members = BaseUserModel.objects.filter(id__in=team_member_ids, role='user')
                    project.team_members.set(team_members)
                
                return Response({
                    "status": status.HTTP_200_OK,
                    "message": "Project updated successfully",
                    "data": ProjectSerializer(project).data
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


class TaskAPIView(APIView):
    """Task CRUD"""
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPagination
    
    def get(self, request, admin_id, pk=None):
        """Get tasks"""
        try:
            admin = get_object_or_404(BaseUserModel, id=admin_id, role='admin')
            
            if pk:
                task = get_object_or_404(Task, id=pk, admin=admin)
                serializer = TaskSerializer(task)
                return Response({
                    "status": status.HTTP_200_OK,
                    "message": "Task fetched successfully",
                    "data": serializer.data
                })
            else:
                queryset = Task.objects.filter(admin=admin)
                
                # Filters
                status_filter = request.query_params.get('status')
                if status_filter:
                    queryset = queryset.filter(status=status_filter)
                
                assigned_to = request.query_params.get('assigned_to')
                if assigned_to:
                    queryset = queryset.filter(assigned_to_id=assigned_to)
                
                project_id = request.query_params.get('project_id')
                if project_id:
                    queryset = queryset.filter(project_id=project_id)
                
                # Pagination
                paginator = self.pagination_class()
                paginated_qs = paginator.paginate_queryset(queryset, request)
                serializer = TaskSerializer(paginated_qs, many=True)
                pagination_data = paginator.get_paginated_response(serializer.data)
                pagination_data["results"] = serializer.data
                pagination_data["message"] = "Tasks fetched successfully"
                
                return Response(pagination_data)
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @transaction.atomic
    def post(self, request, admin_id):
        """Create task"""
        try:
            admin = get_object_or_404(BaseUserModel, id=admin_id, role='admin')
            data = request.data.copy()
            data['admin'] = str(admin.id)
            data['organization'] = str(admin.own_admin_profile.organization.id)
            data['assigned_by'] = str(request.user.id)
            
            serializer = TaskSerializer(data=data)
            if serializer.is_valid():
                task = serializer.save()
                
                # Add dependencies if provided
                dependency_ids = request.data.get('dependency_ids', [])
                if dependency_ids:
                    dependencies = Task.objects.filter(id__in=dependency_ids)
                    task.dependencies.set(dependencies)
                
                return Response({
                    "status": status.HTTP_201_CREATED,
                    "message": "Task created successfully",
                    "data": TaskSerializer(task).data
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
        """Update task"""
        try:
            task = get_object_or_404(Task, id=pk, admin_id=admin_id)
            
            # If status changed to completed, set completed_at
            if 'status' in request.data and request.data['status'] == 'completed' and task.status != 'completed':
                request.data['completed_at'] = timezone.now()
            
            serializer = TaskSerializer(task, data=request.data, partial=True)
            if serializer.is_valid():
                task = serializer.save()
                
                # Update dependencies if provided
                if 'dependency_ids' in request.data:
                    dependency_ids = request.data.get('dependency_ids', [])
                    dependencies = Task.objects.filter(id__in=dependency_ids)
                    task.dependencies.set(dependencies)
                
                return Response({
                    "status": status.HTTP_200_OK,
                    "message": "Task updated successfully",
                    "data": TaskSerializer(task).data
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


class TaskCommentAPIView(APIView):
    """Task Comments"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, task_id):
        """Get task comments"""
        try:
            task = get_object_or_404(Task, id=task_id)
            comments = TaskComment.objects.filter(task=task)
            serializer = TaskCommentSerializer(comments, many=True)
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
    
    def post(self, request, task_id):
        """Create comment"""
        try:
            task = get_object_or_404(Task, id=task_id)
            data = request.data.copy()
            data['task'] = str(task.id)
            data['user'] = str(request.user.id)
            
            serializer = TaskCommentSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                return Response({
                    "status": status.HTTP_201_CREATED,
                    "message": "Comment added successfully",
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


class TaskTimeLogAPIView(APIView):
    """Task Time Logging"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, task_id):
        """Get time logs"""
        try:
            task = get_object_or_404(Task, id=task_id)
            time_logs = TaskTimeLog.objects.filter(task=task)
            serializer = TaskTimeLogSerializer(time_logs, many=True)
            
            # Calculate total time
            total_minutes = sum([log.duration_minutes or 0 for log in time_logs])
            
            return Response({
                "status": status.HTTP_200_OK,
                "message": "Time logs fetched successfully",
                "data": serializer.data,
                "total_minutes": total_minutes
            })
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @transaction.atomic
    def post(self, request, task_id):
        """Create time log"""
        try:
            task = get_object_or_404(Task, id=task_id)
            action = request.data.get('action')  # 'start' or 'stop'
            
            if action == 'start':
                # Create new time log
                time_log = TaskTimeLog.objects.create(
                    task=task,
                    user=request.user,
                    start_time=timezone.now()
                )
                return Response({
                    "status": status.HTTP_201_CREATED,
                    "message": "Time tracking started",
                    "data": TaskTimeLogSerializer(time_log).data
                }, status=status.HTTP_201_CREATED)
            
            elif action == 'stop':
                # Get latest active time log
                time_log = TaskTimeLog.objects.filter(
                    task=task,
                    user=request.user,
                    end_time__isnull=True
                ).order_by('-start_time').first()
                
                if not time_log:
                    return Response({
                        "status": status.HTTP_400_BAD_REQUEST,
                        "message": "No active time log found"
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                time_log.end_time = timezone.now()
                duration = time_log.end_time - time_log.start_time
                time_log.duration_minutes = int(duration.total_seconds() / 60)
                time_log.save()
                
                # Update task actual hours
                task.actual_hours = (task.actual_hours or 0) + (time_log.duration_minutes / 60)
                task.save()
                
                return Response({
                    "status": status.HTTP_200_OK,
                    "message": "Time tracking stopped",
                    "data": TaskTimeLogSerializer(time_log).data
                })
            
            else:
                return Response({
                    "status": status.HTTP_400_BAD_REQUEST,
                    "message": "Invalid action. Use 'start' or 'stop'"
                }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": str(e),
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

