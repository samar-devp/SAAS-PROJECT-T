"""
Task Management URLs
"""

from django.urls import path
from .views import TaskTypeAPIView
from .advanced_views import (
    ProjectAPIView, TaskAPIView, TaskCommentAPIView, TaskTimeLogAPIView
)
from .additional_utility_views import *

urlpatterns = [
    # Task Types
    path('task-types/<uuid:admin_id>', TaskTypeAPIView.as_view(), name='task-type-list-create'),
    path('task-types/<uuid:admin_id>/<int:pk>', TaskTypeAPIView.as_view(), name='task-type-detail'),
    
    # Projects
    path('projects/<uuid:admin_id>', ProjectAPIView.as_view(), name='project-list-create'),
    path('projects/<uuid:admin_id>/<uuid:pk>', ProjectAPIView.as_view(), name='project-detail'),
    
    # Tasks
    path('tasks/<uuid:admin_id>', TaskAPIView.as_view(), name='task-list-create'),
    path('tasks/<uuid:admin_id>/<uuid:pk>', TaskAPIView.as_view(), name='task-detail'),
    
    # Task Comments
    path('task-comments/<uuid:task_id>', TaskCommentAPIView.as_view(), name='task-comments'),
    
    # Task Time Logs
    path('task-time-logs/<uuid:task_id>', TaskTimeLogAPIView.as_view(), name='task-time-logs'),
    
    # Additional Utility APIs
    path('dashboard/<str:org_id>', TaskDashboardAPIView.as_view(), name='task-dashboard'),
    path('employee-tasks/<str:org_id>/<str:employee_id>', EmployeeTaskListAPIView.as_view(), name='employee-tasks'),
    path('projects-list/<str:org_id>', ProjectListAPIView.as_view(), name='projects-list'),
]
