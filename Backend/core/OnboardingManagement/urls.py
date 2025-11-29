"""
Onboarding Management URLs
"""

from django.urls import path
from .views import (
    OnboardingTemplateAPIView, OnboardingChecklistAPIView,
    OnboardingProcessAPIView, OnboardingTaskAPIView,
    DocumentTypeAPIView, EmployeeDocumentAPIView
)
from .additional_utility_views import *

urlpatterns = [
    # Templates
    path('templates/<uuid:org_id>', OnboardingTemplateAPIView.as_view(), name='onboarding-templates'),
    path('templates/<uuid:org_id>/<uuid:pk>', OnboardingTemplateAPIView.as_view(), name='onboarding-template-detail'),
    
    # Checklists
    path('checklists/<uuid:template_id>', OnboardingChecklistAPIView.as_view(), name='onboarding-checklists'),
    
    # Processes
    path('processes/<uuid:org_id>', OnboardingProcessAPIView.as_view(), name='onboarding-processes'),
    path('processes/<uuid:org_id>/<uuid:pk>', OnboardingProcessAPIView.as_view(), name='onboarding-process-detail'),
    
    # Tasks
    path('tasks/<uuid:process_id>', OnboardingTaskAPIView.as_view(), name='onboarding-tasks'),
    path('tasks/<uuid:process_id>/<uuid:pk>', OnboardingTaskAPIView.as_view(), name='onboarding-task-detail'),
    
    # Document Types
    path('document-types/<uuid:org_id>', DocumentTypeAPIView.as_view(), name='document-types'),
    path('document-types/<uuid:org_id>/<uuid:pk>', DocumentTypeAPIView.as_view(), name='document-type-detail'),
    
    # Employee Documents
    path('documents/<uuid:employee_id>', EmployeeDocumentAPIView.as_view(), name='employee-documents'),
    path('documents/<uuid:employee_id>/<uuid:pk>', EmployeeDocumentAPIView.as_view(), name='employee-document-detail'),
    
    # Additional Utility APIs
    path('dashboard/<str:org_id>', OnboardingDashboardAPIView.as_view(), name='onboarding-dashboard'),
]

